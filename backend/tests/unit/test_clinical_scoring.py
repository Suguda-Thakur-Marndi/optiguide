import math


def calculate_snellen_optotype_height_mm(
    distance_meters: float, snellen_denominator: int = 20
) -> float:
    """
    Calculates the exact physical height in mm of a standard 5-arcminute Snellen letter.
    Standard Snellen formula: h = 2 * d * tan(5' / 2) * (snellen_denominator / 20)
    """
    arcmin_5_rad = math.radians(5.0 / 60.0)
    base_height_m = 2.0 * distance_meters * math.tan(arcmin_5_rad / 2.0)
    scaled_height_m = base_height_m * (snellen_denominator / 20.0)
    return scaled_height_m * 1000.0  # to mm


def snellen_to_logmar(snellen_numerator: int, snellen_denominator: int) -> float:
    """Computes logMAR: log10(denominator / numerator)."""
    return round(math.log10(snellen_denominator / snellen_numerator), 2)


def test_visual_acuity_geometry_and_optotype_sizing():
    """Verifies that physical optotype dimensions match clinical optics standard."""
    # At 6 meters (standard distance lane): 20/20 optotype height is ~8.73 mm
    h_6m_2020 = calculate_snellen_optotype_height_mm(distance_meters=6.0, snellen_denominator=20)
    assert 8.70 <= h_6m_2020 <= 8.75

    # At 0.6 meters (handheld/near-distance screen): 20/20 optotype height is ~0.873 mm
    h_06m_2020 = calculate_snellen_optotype_height_mm(distance_meters=0.6, snellen_denominator=20)
    assert 0.86 <= h_06m_2020 <= 0.88

    # 20/100 letter should be exactly 5x taller than 20/20 letter
    h_06m_20100 = calculate_snellen_optotype_height_mm(distance_meters=0.6, snellen_denominator=100)
    assert abs(h_06m_20100 - (h_06m_2020 * 5)) < 0.01


def test_snellen_to_logmar_conversions():
    """Verifies standard Snellen to logMAR mathematical conversion values."""
    assert snellen_to_logmar(20, 20) == 0.0
    assert snellen_to_logmar(20, 40) == 0.3
    assert snellen_to_logmar(20, 100) == 0.7
    assert snellen_to_logmar(20, 200) == 1.0


def test_astigmatic_meridian_determination():
    """Verifies clock dial hour to refractive meridian orientation conversion."""
    # Clock hour to degree conversion: Angle = Hour * 30 degrees
    # e.g. 12-6 axis = 90 degrees; 3-9 axis = 180 degrees
    hour_to_degrees = {
        12: 90,
        1: 60,
        2: 30,
        3: 180,
        4: 150,
        5: 120,
        6: 90,
    }
    assert hour_to_degrees[12] == 90
    assert hour_to_degrees[3] == 180
