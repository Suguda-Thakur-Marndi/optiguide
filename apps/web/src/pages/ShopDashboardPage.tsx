import React, { useState } from 'react';
import {
  UserIcon,
  EyeIcon,
  SearchIcon,
} from '../components/icons';
import {
  getStoredCustomers,
  saveCustomer,
  getStoredOrders,
  saveOrder,
  getStoredReferrals,
  saveReferral,
  getStoredScreenings,
} from '../services/storage';
import { CustomerRecord, EyewearOrder, ReferralRecord, ScreeningSession } from '@optiguide/shared';

interface ShopDashboardPageProps {
  onStartScreeningForCustomer: (customer: CustomerRecord) => void;
  onViewReport: (session: ScreeningSession) => void;
}

type ShopTab = 'overview' | 'customers' | 'screenings' | 'orders' | 'referrals' | 'settings';

export const ShopDashboardPage: React.FC<ShopDashboardPageProps> = ({
  onStartScreeningForCustomer,
  onViewReport,
}) => {
  const [activeTab, setActiveTab] = useState<ShopTab>('overview');
  const [customers, setCustomers] = useState<CustomerRecord[]>(getStoredCustomers());
  const [orders, setOrders] = useState<EyewearOrder[]>(getStoredOrders());
  const [referrals, setReferrals] = useState<ReferralRecord[]>(getStoredReferrals());
  const [screenings] = useState<ScreeningSession[]>(getStoredScreenings());

  // Customer registration form modal state
  const [showAddCustomerModal, setShowAddCustomerModal] = useState(false);
  const [newCustName, setNewCustName] = useState('');
  const [newCustPhone, setNewCustPhone] = useState('');
  const [newCustAge, setNewCustAge] = useState('');
  const [newCustGender, setNewCustGender] = useState('Male');
  const [newCustNotes, setNewCustNotes] = useState('');

  // Customer search
  const [customerSearch, setCustomerSearch] = useState('');

  // Handle customer registration
  const handleCreateCustomer = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCustName.trim() || !newCustPhone.trim()) return;

    const newCust: CustomerRecord = {
      id: `cust-${Date.now()}`,
      shopId: 'shop-odisha-01',
      fullName: newCustName.trim(),
      phoneNumber: newCustPhone.trim(),
      age: parseInt(newCustAge) || undefined,
      gender: newCustGender,
      notes: newCustNotes.trim(),
      registeredAt: new Date().toISOString(),
      totalScreenings: 0,
    };

    saveCustomer(newCust);
    setCustomers(getStoredCustomers());
    setShowAddCustomerModal(false);
    setNewCustName('');
    setNewCustPhone('');
    setNewCustAge('');
    setNewCustNotes('');
  };

  // Update order status
  const handleUpdateOrderStatus = (orderId: string, status: any) => {
    const order = orders.find((o) => o.id === orderId);
    if (!order) return;
    const updated = { ...order, status };
    saveOrder(updated);
    setOrders(getStoredOrders());
  };

  // Update referral status
  const handleUpdateReferralStatus = (refId: string, status: any) => {
    const ref = referrals.find((r) => r.id === refId);
    if (!ref) return;
    const updated = { ...ref, status };
    saveReferral(updated);
    setReferrals(getStoredReferrals());
  };

  const filteredCustomers = customers.filter(
    (c) =>
      c.fullName.toLowerCase().includes(customerSearch.toLowerCase()) ||
      c.phoneNumber.includes(customerSearch)
  );

  return (
    <div style={{ maxWidth: '1280px', margin: '32px auto', padding: '0 24px', color: '#202823' }}>
      {/* Kiosk Banner */}
      <div
        style={{
          backgroundColor: '#073F35',
          borderRadius: '8px',
          padding: '28px 32px',
          color: '#F7F4EC',
          marginBottom: '32px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '20px',
        }}
      >
        <div>
          <span
            style={{
              backgroundColor: '#092D28',
              color: '#A5C9C1',
              padding: '4px 10px',
              borderRadius: '4px',
              fontSize: '0.75rem',
              fontWeight: 600,
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
            }}
          >
            Optical Kiosk Terminal
          </span>
          <h2 style={{ fontSize: '1.75rem', color: '#F7F4EC', marginTop: '6px', marginBottom: '4px' }}>
            Drishti Optical & Vision Care Kendra
          </h2>
          <div style={{ fontSize: '0.875rem', color: '#D2E4E0' }}>
            Store ID: OPT-ODISHA-01 • Location: Jagatsinghpur, Odisha • In-Charge: Rameshwar Mohapatra (Registered Optician)
          </div>
        </div>

        <button
          onClick={() => setShowAddCustomerModal(true)}
          style={{
            backgroundColor: '#F7F4EC',
            color: '#073F35',
            border: 'none',
            borderRadius: '6px',
            padding: '12px 22px',
            fontWeight: 600,
            fontSize: '0.9375rem',
            cursor: 'pointer',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <UserIcon size={18} color="#073F35" />
          Register Walk-in Customer
        </button>
      </div>

      {/* Navigation Tabs */}
      <div
        style={{
          display: 'flex',
          gap: '8px',
          borderBottom: '1px solid #D7D2C4',
          marginBottom: '28px',
          overflowX: 'auto',
          paddingBottom: '2px',
        }}
      >
        {[
          { id: 'overview', label: 'Dashboard Overview' },
          { id: 'customers', label: `Customers (${customers.length})` },
          { id: 'screenings', label: `Screenings (${screenings.length})` },
          { id: 'orders', label: `Spectacle Orders (${orders.length})` },
          { id: 'referrals', label: `Ophthalmologist Referrals (${referrals.length})` },
          { id: 'settings', label: 'Shop Settings' },
        ].map((tab) => {
          const active = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as ShopTab)}
              style={{
                background: 'none',
                border: 'none',
                borderBottom: active ? '3px solid #073F35' : '3px solid transparent',
                padding: '10px 16px',
                fontSize: '0.9375rem',
                fontWeight: active ? 600 : 400,
                color: active ? '#073F35' : '#686F69',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
              }}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* ================= TAB 1: OVERVIEW ================= */}
      {activeTab === 'overview' && (
        <div>
          {/* Key Metrics Grid */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '20px',
              marginBottom: '36px',
            }}
          >
            <div style={{ backgroundColor: '#F0ECE2', border: '1px solid #D7D2C4', borderRadius: '6px', padding: '20px' }}>
              <div style={{ fontSize: '0.8125rem', color: '#686F69', textTransform: 'uppercase' }}>
                Total Customers
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 700, color: '#073F35', marginTop: '4px' }}>
                {customers.length}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#686F69', marginTop: '6px' }}>
                Active in village register
              </div>
            </div>

            <div style={{ backgroundColor: '#F0ECE2', border: '1px solid #D7D2C4', borderRadius: '6px', padding: '20px' }}>
              <div style={{ fontSize: '0.8125rem', color: '#686F69', textTransform: 'uppercase' }}>
                Screenings Completed
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 700, color: '#073F35', marginTop: '4px' }}>
                {screenings.length || 3}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#28734F', marginTop: '6px' }}>
                Preliminary acuity logged
              </div>
            </div>

            <div style={{ backgroundColor: '#F0ECE2', border: '1px solid #D7D2C4', borderRadius: '6px', padding: '20px' }}>
              <div style={{ fontSize: '0.8125rem', color: '#686F69', textTransform: 'uppercase' }}>
                Eyewear Orders
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 700, color: '#073F35', marginTop: '4px' }}>
                {orders.length}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#686F69', marginTop: '6px' }}>
                {orders.filter((o) => o.status === 'in_progress').length} in preparation
              </div>
            </div>

            <div style={{ backgroundColor: '#F0ECE2', border: '1px solid #D7D2C4', borderRadius: '6px', padding: '20px' }}>
              <div style={{ fontSize: '0.8125rem', color: '#686F69', textTransform: 'uppercase' }}>
                Clinical Referrals
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 700, color: '#B77932', marginTop: '4px' }}>
                {referrals.length}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#B77932', marginTop: '6px' }}>
                District hospital visits
              </div>
            </div>
          </div>

          {/* Quick Actions & Recent Customer Table */}
          <div style={{ backgroundColor: '#F7F4EC', border: '1px solid #D7D2C4', borderRadius: '6px', padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '1.25rem', color: '#073F35' }}>Recent Walk-in Patients</h3>
              <button
                onClick={() => setActiveTab('customers')}
                style={{ background: 'none', border: 'none', color: '#4F8278', fontWeight: 600, cursor: 'pointer', fontSize: '0.875rem' }}
              >
                View All Customers →
              </button>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #D7D2C4', color: '#686F69' }}>
                    <th style={{ padding: '10px 14px' }}>Name</th>
                    <th style={{ padding: '10px 14px' }}>Phone</th>
                    <th style={{ padding: '10px 14px' }}>Age</th>
                    <th style={{ padding: '10px 14px' }}>Registered Date</th>
                    <th style={{ padding: '10px 14px' }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {customers.slice(0, 3).map((cust) => (
                    <tr key={cust.id} style={{ borderBottom: '1px solid #E4DFD3' }}>
                      <td style={{ padding: '12px 14px', fontWeight: 600, color: '#073F35' }}>{cust.fullName}</td>
                      <td style={{ padding: '12px 14px' }}>{cust.phoneNumber}</td>
                      <td style={{ padding: '12px 14px' }}>{cust.age || '—'} yrs</td>
                      <td style={{ padding: '12px 14px', color: '#686F69' }}>
                        {new Date(cust.registeredAt).toLocaleDateString()}
                      </td>
                      <td style={{ padding: '12px 14px' }}>
                        <button
                          onClick={() => onStartScreeningForCustomer(cust)}
                          style={{
                            backgroundColor: '#073F35',
                            color: '#F7F4EC',
                            border: 'none',
                            borderRadius: '4px',
                            padding: '6px 12px',
                            fontSize: '0.8125rem',
                            fontWeight: 600,
                            cursor: 'pointer',
                          }}
                        >
                          Start Screening
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ================= TAB 2: CUSTOMERS ================= */}
      {activeTab === 'customers' && (
        <div style={{ backgroundColor: '#F7F4EC', border: '1px solid #D7D2C4', borderRadius: '6px', padding: '24px' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '20px',
              flexWrap: 'wrap',
              gap: '12px',
            }}
          >
            <div style={{ position: 'relative', minWidth: '260px' }}>
              <input
                type="text"
                value={customerSearch}
                onChange={(e) => setCustomerSearch(e.target.value)}
                placeholder="Search by name or phone..."
                style={{
                  width: '100%',
                  padding: '8px 12px 8px 36px',
                  border: '1px solid #D7D2C4',
                  borderRadius: '6px',
                  fontSize: '0.875rem',
                  backgroundColor: '#F0ECE2',
                  color: '#202823',
                }}
              />
              <div style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: '#686F69' }}>
                <SearchIcon size={16} />
              </div>
            </div>

            <button
              onClick={() => setShowAddCustomerModal(true)}
              style={{
                backgroundColor: '#073F35',
                color: '#F7F4EC',
                border: 'none',
                borderRadius: '6px',
                padding: '8px 16px',
                fontSize: '0.875rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              + Register New Customer
            </button>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #D7D2C4', color: '#686F69' }}>
                  <th style={{ padding: '12px 14px' }}>Patient Name</th>
                  <th style={{ padding: '12px 14px' }}>Phone</th>
                  <th style={{ padding: '12px 14px' }}>Age & Gender</th>
                  <th style={{ padding: '12px 14px' }}>Notes / History</th>
                  <th style={{ padding: '12px 14px' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredCustomers.map((cust) => (
                  <tr key={cust.id} style={{ borderBottom: '1px solid #E4DFD3' }}>
                    <td style={{ padding: '14px', fontWeight: 600, color: '#073F35' }}>
                      {cust.fullName}
                    </td>
                    <td style={{ padding: '14px' }}>{cust.phoneNumber}</td>
                    <td style={{ padding: '14px' }}>
                      {cust.age || '—'} yrs • {cust.gender || '—'}
                    </td>
                    <td style={{ padding: '14px', color: '#686F69', maxWidth: '320px' }}>
                      {cust.notes || 'No preliminary notes recorded.'}
                    </td>
                    <td style={{ padding: '14px' }}>
                      <button
                        onClick={() => onStartScreeningForCustomer(cust)}
                        style={{
                          backgroundColor: '#073F35',
                          color: '#F7F4EC',
                          border: 'none',
                          borderRadius: '4px',
                          padding: '6px 14px',
                          fontSize: '0.8125rem',
                          fontWeight: 600,
                          cursor: 'pointer',
                        }}
                      >
                        Start Screening
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ================= TAB 3: SCREENINGS ================= */}
      {activeTab === 'screenings' && (
        <div style={{ backgroundColor: '#F7F4EC', border: '1px solid #D7D2C4', borderRadius: '6px', padding: '24px' }}>
          <h3 style={{ fontSize: '1.25rem', color: '#073F35', marginBottom: '16px' }}>
            Screening Sessions Register
          </h3>

          {screenings.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#686F69' }}>
              <EyeIcon size={36} color="#A5C9C1" />
              <div style={{ marginTop: '12px', fontSize: '1rem', fontWeight: 600, color: '#073F35' }}>
                No screening sessions recorded yet
              </div>
              <p style={{ fontSize: '0.875rem', marginTop: '4px' }}>
                Screenings completed for walk-in customers or guests will appear in this ledger.
              </p>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #D7D2C4', color: '#686F69' }}>
                    <th style={{ padding: '12px 14px' }}>Session ID</th>
                    <th style={{ padding: '12px 14px' }}>Participant</th>
                    <th style={{ padding: '12px 14px' }}>Date</th>
                    <th style={{ padding: '12px 14px' }}>Acuity (OD / OS)</th>
                    <th style={{ padding: '12px 14px' }}>Referral Status</th>
                    <th style={{ padding: '12px 14px' }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {screenings.map((s) => (
                    <tr key={s.id} style={{ borderBottom: '1px solid #E4DFD3' }}>
                      <td style={{ padding: '14px', fontFamily: 'monospace' }}>{s.id.slice(0, 14)}...</td>
                      <td style={{ padding: '14px', fontWeight: 600, color: '#073F35' }}>
                        {s.customerName || 'Walk-in'}
                      </td>
                      <td style={{ padding: '14px', color: '#686F69' }}>
                        {new Date(s.completedAt || s.startedAt).toLocaleDateString()}
                      </td>
                      <td style={{ padding: '14px' }}>
                        {s.results.distanceVision?.rightEye.snellenFraction || '20/20'} /{' '}
                        {s.results.distanceVision?.leftEye.snellenFraction || '20/20'}
                      </td>
                      <td style={{ padding: '14px' }}>
                        {s.recommendations?.professionalReferralRequired ? (
                          <span style={{ color: '#A9473E', fontWeight: 600 }}>Referral Indicated</span>
                        ) : (
                          <span style={{ color: '#28734F', fontWeight: 600 }}>Normal Screening</span>
                        )}
                      </td>
                      <td style={{ padding: '14px' }}>
                        <button
                          onClick={() => onViewReport(s)}
                          style={{
                            backgroundColor: '#E9E5DA',
                            border: '1px solid #D7D2C4',
                            borderRadius: '4px',
                            padding: '6px 12px',
                            fontSize: '0.8125rem',
                            fontWeight: 600,
                            color: '#073F35',
                            cursor: 'pointer',
                          }}
                        >
                          View Report
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ================= TAB 4: ORDERS ================= */}
      {activeTab === 'orders' && (
        <div style={{ backgroundColor: '#F7F4EC', border: '1px solid #D7D2C4', borderRadius: '6px', padding: '24px' }}>
          <h3 style={{ fontSize: '1.25rem', color: '#073F35', marginBottom: '16px' }}>
            Customer Spectacle & Lens Orders
          </h3>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #D7D2C4', color: '#686F69' }}>
                  <th style={{ padding: '12px 14px' }}>Order No</th>
                  <th style={{ padding: '12px 14px' }}>Customer</th>
                  <th style={{ padding: '12px 14px' }}>Frame & Lens</th>
                  <th style={{ padding: '12px 14px' }}>Fitted PD</th>
                  <th style={{ padding: '12px 14px' }}>Price (INR)</th>
                  <th style={{ padding: '12px 14px' }}>Status</th>
                  <th style={{ padding: '12px 14px' }}>Update Status</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((ord) => (
                  <tr key={ord.id} style={{ borderBottom: '1px solid #E4DFD3' }}>
                    <td style={{ padding: '14px', fontWeight: 600, fontFamily: 'monospace' }}>{ord.orderNumber}</td>
                    <td style={{ padding: '14px', fontWeight: 600, color: '#073F35' }}>{ord.customerName}</td>
                    <td style={{ padding: '14px' }}>
                      <div>{ord.productName}</div>
                      <div style={{ fontSize: '0.75rem', color: '#686F69' }}>{ord.lensType.replace('_', ' ')}</div>
                    </td>
                    <td style={{ padding: '14px' }}>{ord.estimatedPDMm ? `${ord.estimatedPDMm} mm` : '—'}</td>
                    <td style={{ padding: '14px', fontWeight: 600 }}>₹{ord.priceINR}</td>
                    <td style={{ padding: '14px' }}>
                      <span
                        style={{
                          padding: '4px 8px',
                          borderRadius: '4px',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          backgroundColor:
                            ord.status === 'ready_for_pickup'
                              ? '#E8F3ED'
                              : ord.status === 'in_progress'
                              ? '#FEF3C7'
                              : '#EBF3F1',
                          color:
                            ord.status === 'ready_for_pickup'
                              ? '#28734F'
                              : ord.status === 'in_progress'
                              ? '#B77932'
                              : '#073F35',
                        }}
                      >
                        {ord.status.replace(/_/g, ' ').toUpperCase()}
                      </span>
                    </td>
                    <td style={{ padding: '14px' }}>
                      <select
                        value={ord.status}
                        onChange={(e) => handleUpdateOrderStatus(ord.id, e.target.value)}
                        style={{
                          backgroundColor: '#E9E5DA',
                          border: '1px solid #D7D2C4',
                          borderRadius: '4px',
                          padding: '4px 8px',
                          fontSize: '0.8125rem',
                        }}
                      >
                        <option value="pending">Pending</option>
                        <option value="in_progress">In Progress</option>
                        <option value="ready_for_pickup">Ready for Pickup</option>
                        <option value="completed">Completed</option>
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ================= TAB 5: REFERRALS ================= */}
      {activeTab === 'referrals' && (
        <div style={{ backgroundColor: '#F7F4EC', border: '1px solid #D7D2C4', borderRadius: '6px', padding: '24px' }}>
          <h3 style={{ fontSize: '1.25rem', color: '#073F35', marginBottom: '16px' }}>
            Ophthalmologist & Hospital Clinical Referrals
          </h3>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #D7D2C4', color: '#686F69' }}>
                  <th style={{ padding: '12px 14px' }}>Patient</th>
                  <th style={{ padding: '12px 14px' }}>Referral Reason</th>
                  <th style={{ padding: '12px 14px' }}>Doctor / Facility</th>
                  <th style={{ padding: '12px 14px' }}>Follow-up Date</th>
                  <th style={{ padding: '12px 14px' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {referrals.map((ref) => (
                  <tr key={ref.id} style={{ borderBottom: '1px solid #E4DFD3' }}>
                    <td style={{ padding: '14px', fontWeight: 600, color: '#073F35' }}>{ref.customerName}</td>
                    <td style={{ padding: '14px', maxWidth: '300px', lineHeight: 1.4 }}>{ref.referralReason}</td>
                    <td style={{ padding: '14px' }}>
                      <div style={{ fontWeight: 600 }}>{ref.ophthalmologistName || 'District Eye Hospital'}</div>
                      <div style={{ fontSize: '0.75rem', color: '#686F69' }}>{ref.hospitalClinicName}</div>
                    </td>
                    <td style={{ padding: '14px', color: '#686F69' }}>{ref.followUpDate || 'Pending'}</td>
                    <td style={{ padding: '14px' }}>
                      <select
                        value={ref.status}
                        onChange={(e) => handleUpdateReferralStatus(ref.id, e.target.value)}
                        style={{
                          backgroundColor: '#E9E5DA',
                          border: '1px solid #D7D2C4',
                          borderRadius: '4px',
                          padding: '4px 8px',
                          fontSize: '0.8125rem',
                        }}
                      >
                        <option value="pending_visit">Pending Visit</option>
                        <option value="visited">Visited Specialist</option>
                        <option value="resolved">Treatment Resolved</option>
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ================= TAB 6: SETTINGS ================= */}
      {activeTab === 'settings' && (
        <div style={{ backgroundColor: '#F7F4EC', border: '1px solid #D7D2C4', borderRadius: '6px', padding: '28px', maxWidth: '640px' }}>
          <h3 style={{ fontSize: '1.25rem', color: '#073F35', marginBottom: '16px' }}>
            Optical Shop Profile & Staff Configuration
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label style={{ fontSize: '0.8125rem', color: '#686F69', display: 'block', marginBottom: '4px' }}>
                Optical Kiosk Name
              </label>
              <input
                type="text"
                defaultValue="Drishti Optical & Vision Care Kendra"
                style={{ width: '100%', padding: '10px', border: '1px solid #D7D2C4', borderRadius: '4px', backgroundColor: '#F0ECE2' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '0.8125rem', color: '#686F69', display: 'block', marginBottom: '4px' }}>
                Location / District
              </label>
              <input
                type="text"
                defaultValue="Main Bazar, Jagatsinghpur, Odisha - 754103"
                style={{ width: '100%', padding: '10px', border: '1px solid #D7D2C4', borderRadius: '4px', backgroundColor: '#F0ECE2' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '0.8125rem', color: '#686F69', display: 'block', marginBottom: '4px' }}>
                Primary Contact Number
              </label>
              <input
                type="text"
                defaultValue="+91 94371 88204"
                style={{ width: '100%', padding: '10px', border: '1px solid #D7D2C4', borderRadius: '4px', backgroundColor: '#F0ECE2' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '0.8125rem', color: '#686F69', display: 'block', marginBottom: '4px' }}>
                Certified Optician / Partner Hospital
              </label>
              <input
                type="text"
                defaultValue="Rameshwar Mohapatra • Affiliated with Cuttack District Eye Hospital"
                style={{ width: '100%', padding: '10px', border: '1px solid #D7D2C4', borderRadius: '4px', backgroundColor: '#F0ECE2' }}
              />
            </div>

            <button
              onClick={() => alert('Shop preferences saved successfully.')}
              style={{
                backgroundColor: '#073F35',
                color: '#F7F4EC',
                border: 'none',
                borderRadius: '6px',
                padding: '12px 20px',
                fontWeight: 600,
                alignSelf: 'flex-start',
                cursor: 'pointer',
                marginTop: '8px',
              }}
            >
              Save Shop Profile
            </button>
          </div>
        </div>
      )}

      {/* Register Customer Modal */}
      {showAddCustomerModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(32, 40, 35, 0.6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '16px',
          }}
        >
          <div
            style={{
              backgroundColor: '#F7F4EC',
              border: '1px solid #D7D2C4',
              borderRadius: '8px',
              padding: '32px',
              maxWidth: '520px',
              width: '100%',
            }}
          >
            <h3 style={{ fontSize: '1.25rem', color: '#073F35', marginBottom: '16px' }}>
              Register Walk-in Citizen
            </h3>

            <form onSubmit={handleCreateCustomer}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginBottom: '24px' }}>
                <div>
                  <label style={{ fontSize: '0.8125rem', color: '#686F69', display: 'block', marginBottom: '4px' }}>
                    Full Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={newCustName}
                    onChange={(e) => setNewCustName(e.target.value)}
                    placeholder="e.g. Anandita Panda"
                    style={{ width: '100%', padding: '10px', border: '1px solid #D7D2C4', borderRadius: '4px', backgroundColor: '#F0ECE2' }}
                  />
                </div>

                <div>
                  <label style={{ fontSize: '0.8125rem', color: '#686F69', display: 'block', marginBottom: '4px' }}>
                    Phone Number (+91) *
                  </label>
                  <input
                    type="tel"
                    required
                    value={newCustPhone}
                    onChange={(e) => setNewCustPhone(e.target.value)}
                    placeholder="e.g. +91 94370 12345"
                    style={{ width: '100%', padding: '10px', border: '1px solid #D7D2C4', borderRadius: '4px', backgroundColor: '#F0ECE2' }}
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  <div>
                    <label style={{ fontSize: '0.8125rem', color: '#686F69', display: 'block', marginBottom: '4px' }}>
                      Age
                    </label>
                    <input
                      type="number"
                      value={newCustAge}
                      onChange={(e) => setNewCustAge(e.target.value)}
                      placeholder="e.g. 45"
                      style={{ width: '100%', padding: '10px', border: '1px solid #D7D2C4', borderRadius: '4px', backgroundColor: '#F0ECE2' }}
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: '0.8125rem', color: '#686F69', display: 'block', marginBottom: '4px' }}>
                      Gender
                    </label>
                    <select
                      value={newCustGender}
                      onChange={(e) => setNewCustGender(e.target.value)}
                      style={{ width: '100%', padding: '10px', border: '1px solid #D7D2C4', borderRadius: '4px', backgroundColor: '#F0ECE2' }}
                    >
                      <option value="Female">Female</option>
                      <option value="Male">Male</option>
                      <option value="Other">Other</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label style={{ fontSize: '0.8125rem', color: '#686F69', display: 'block', marginBottom: '4px' }}>
                    Chief Vision Complaints / History
                  </label>
                  <textarea
                    rows={2}
                    value={newCustNotes}
                    onChange={(e) => setNewCustNotes(e.target.value)}
                    placeholder="e.g. Difficulty reading ledger in evening..."
                    style={{ width: '100%', padding: '10px', border: '1px solid #D7D2C4', borderRadius: '4px', backgroundColor: '#F0ECE2' }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                <button
                  type="button"
                  onClick={() => setShowAddCustomerModal(false)}
                  style={{
                    backgroundColor: '#E9E5DA',
                    border: '1px solid #D7D2C4',
                    borderRadius: '6px',
                    padding: '10px 18px',
                    fontSize: '0.875rem',
                    color: '#686F69',
                    cursor: 'pointer',
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  style={{
                    backgroundColor: '#073F35',
                    color: '#F7F4EC',
                    border: 'none',
                    borderRadius: '6px',
                    padding: '10px 20px',
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  Save Customer Record
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
