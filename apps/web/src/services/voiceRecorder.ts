/**
 * OptiGuide Browser Voice & Microphone Recording Utility
 *
 * Implements in-browser audio capture and standard 16-bit mono PCM WAV
 * encoding (16,000 Hz) compatible with the OptiGuide speech recognition pipeline.
 *
 * Safe for localhost development and production HTTPS.
 */

export interface RecordedAudioResult {
  blob: Blob;
  base64: string;
  durationMs: number;
}

export type MicState = 'idle' | 'requesting' | 'listening' | 'processing' | 'denied' | 'unsupported';

class VoiceRecorderService {
  private audioContext: AudioContext | null = null;
  private mediaStream: MediaStream | null = null;
  private audioInput: MediaStreamAudioSourceNode | null = null;
  private scriptProcessor: ScriptProcessorNode | null = null;
  private audioBuffers: Float32Array[] = [];
  private recordingStartTime: number = 0;
  private activeState: MicState = 'idle';
  private currentVolume: number = 0;
  private volumeCallback: ((volume: number) => void) | null = null;
  private autoStopTimeout: any = null;

  public isSupported(): boolean {
    return Boolean(
      typeof window !== 'undefined' &&
        navigator.mediaDevices &&
        typeof navigator.mediaDevices.getUserMedia === 'function' &&
        (window.AudioContext || (window as any).webkitAudioContext)
    );
  }

  public getState(): MicState {
    return this.activeState;
  }

  public onVolumeChange(cb: (vol: number) => void) {
    this.volumeCallback = cb;
  }

  /**
   * Prompts user for microphone permission without starting a recording.
   */
  public async requestPermission(): Promise<boolean> {
    if (!this.isSupported()) {
      this.activeState = 'unsupported';
      return false;
    }

    this.activeState = 'requesting';
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      // Immediately stop temporary permission stream
      stream.getTracks().forEach((track) => track.stop());
      this.activeState = 'idle';
      return true;
    } catch (err: any) {
      if (err?.name === 'NotAllowedError' || err?.name === 'PermissionDeniedError') {
        this.activeState = 'denied';
      } else {
        this.activeState = 'unsupported';
      }
      return false;
    }
  }

  /**
   * Starts capturing microphone audio at 16,000 Hz mono.
   * Automatically invokes onAutoStop after maxDurationMs if speech finishes.
   */
  public async startRecording(
    maxDurationMs: number = 4000,
    onAutoStop?: (result: RecordedAudioResult) => void
  ): Promise<void> {
    if (this.activeState === 'listening') {
      return;
    }

    if (!this.isSupported()) {
      this.activeState = 'unsupported';
      throw new Error('Microphone audio recording is not supported in this browser.');
    }

    try {
      this.activeState = 'requesting';
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      this.audioContext = new AudioCtx({ sampleRate: 16000 });
      this.audioInput = this.audioContext.createMediaStreamSource(this.mediaStream);

      // 4096 sample buffer size for low latency volume and chunk gathering
      this.scriptProcessor = this.audioContext.createScriptProcessor(4096, 1, 1);
      this.audioBuffers = [];
      this.recordingStartTime = performance.now();

      this.scriptProcessor.onaudioprocess = (e) => {
        if (this.activeState !== 'listening') return;
        const channelData = e.inputBuffer.getChannelData(0);
        this.audioBuffers.push(new Float32Array(channelData));

        // Compute RMS volume for reactive audio waveform indicator
        let sumSquares = 0;
        for (let i = 0; i < channelData.length; i++) {
          sumSquares += channelData[i] * channelData[i];
        }
        const rms = Math.sqrt(sumSquares / channelData.length);
        this.currentVolume = Math.min(1.0, rms * 5.0); // Boost scale for UI visibility

        if (this.volumeCallback) {
          this.volumeCallback(this.currentVolume);
        }
      };

      this.audioInput.connect(this.scriptProcessor);
      this.scriptProcessor.connect(this.audioContext.destination);
      this.activeState = 'listening';

      // Auto-stop after maximum duration so patient doesn't have to click "done" every optotype
      if (maxDurationMs > 0) {
        this.autoStopTimeout = setTimeout(async () => {
          if (this.activeState === 'listening') {
            const res = await this.stopRecording();
            if (onAutoStop) onAutoStop(res);
          }
        }, maxDurationMs);
      }
    } catch (err: any) {
      this.cleanup();
      if (err?.name === 'NotAllowedError' || err?.name === 'PermissionDeniedError') {
        this.activeState = 'denied';
        throw new Error('Microphone permission was denied. Please allow microphone access to use voice controls.');
      } else {
        this.activeState = 'unsupported';
        throw new Error(err?.message || 'Failed to initialize microphone audio stream.');
      }
    }
  }

  /**
   * Stops microphone recording and generates PCM WAV result.
   */
  public async stopRecording(): Promise<RecordedAudioResult> {
    if (this.autoStopTimeout) {
      clearTimeout(this.autoStopTimeout);
      this.autoStopTimeout = null;
    }

    if (this.activeState !== 'listening' && this.audioBuffers.length === 0) {
      this.cleanup();
      this.activeState = 'idle';
      throw new Error('No audio was captured.');
    }

    this.activeState = 'processing';
    const durationMs = performance.now() - this.recordingStartTime;

    // Disconnect audio nodes
    if (this.scriptProcessor) {
      this.scriptProcessor.disconnect();
      this.scriptProcessor = null;
    }
    if (this.audioInput) {
      this.audioInput.disconnect();
      this.audioInput = null;
    }

    // Stop all media tracks immediately so microphone light turns off
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => track.stop());
      this.mediaStream = null;
    }

    // Close audio context
    if (this.audioContext) {
      try {
        await this.audioContext.close();
      } catch {
        // Ignore context close error
      }
      this.audioContext = null;
    }

    // Merge float audio samples
    const totalSamples = this.audioBuffers.reduce((acc, b) => acc + b.length, 0);
    const mergedSamples = new Float32Array(totalSamples);
    let offset = 0;
    for (const buf of this.audioBuffers) {
      mergedSamples.set(buf, offset);
      offset += buf.length;
    }

    // Encode to 16-bit PCM WAV at 16000 Hz
    const wavBlob = this.encodeWav(mergedSamples, 16000);
    const base64 = await this.blobToBase64(wavBlob);

    this.cleanup();
    this.activeState = 'idle';

    return {
      blob: wavBlob,
      base64,
      durationMs,
    };
  }

  public cancelRecording(): void {
    if (this.autoStopTimeout) {
      clearTimeout(this.autoStopTimeout);
      this.autoStopTimeout = null;
    }
    this.cleanup();
    this.activeState = 'idle';
  }

  private cleanup(): void {
    if (this.scriptProcessor) {
      try {
        this.scriptProcessor.disconnect();
      } catch {}
      this.scriptProcessor = null;
    }
    if (this.audioInput) {
      try {
        this.audioInput.disconnect();
      } catch {}
      this.audioInput = null;
    }
    if (this.mediaStream) {
      try {
        this.mediaStream.getTracks().forEach((t) => t.stop());
      } catch {}
      this.mediaStream = null;
    }
    if (this.audioContext) {
      try {
        this.audioContext.close();
      } catch {}
      this.audioContext = null;
    }
    this.audioBuffers = [];
    this.currentVolume = 0;
  }

  /**
   * Encodes raw PCM float32 samples into standard 16-bit mono PCM WAV.
   */
  public encodeWav(samples: Float32Array, sampleRate: number = 16000): Blob {
    const dataLength = samples.length * 2;
    const buffer = new ArrayBuffer(44 + dataLength);
    const view = new DataView(buffer);

    // RIFF chunk descriptor
    this.writeAsciiString(view, 0, 'RIFF');
    view.setUint32(4, 36 + dataLength, true);
    this.writeAsciiString(view, 8, 'WAVE');

    // fmt sub-chunk
    this.writeAsciiString(view, 12, 'fmt ');
    view.setUint32(16, 16, true); // SubChunk1Size (16 for PCM)
    view.setUint16(20, 1, true); // AudioFormat (1 = PCM)
    view.setUint16(22, 1, true); // NumChannels (1 = Mono)
    view.setUint32(24, sampleRate, true); // SampleRate
    view.setUint32(28, sampleRate * 2, true); // ByteRate (SampleRate * 1 channel * 2 bytes)
    view.setUint16(32, 2, true); // BlockAlign (1 channel * 2 bytes)
    view.setUint16(34, 16, true); // BitsPerSample (16-bit)

    // data sub-chunk
    this.writeAsciiString(view, 36, 'data');
    view.setUint32(40, dataLength, true);

    // Write 16-bit clamped PCM audio data
    let writeOffset = 44;
    for (let i = 0; i < samples.length; i++, writeOffset += 2) {
      const s = Math.max(-1, Math.min(1, samples[i]));
      view.setInt16(writeOffset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    }

    return new Blob([view], { type: 'audio/wav' });
  }

  private writeAsciiString(view: DataView, offset: number, text: string): void {
    for (let i = 0; i < text.length; i++) {
      view.setUint8(offset + i, text.charCodeAt(i));
    }
  }

  private blobToBase64(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        if (typeof reader.result === 'string') {
          const parts = reader.result.split(',');
          resolve(parts[1] || parts[0]);
        } else {
          reject(new Error('Failed to convert WAV blob to base64.'));
        }
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }
}

export const voiceRecorder = new VoiceRecorderService();
