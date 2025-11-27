import { useState, useEffect } from "react";
import axios from "axios";
import { API_URL } from "./config";
import "./Payment.css";

export default function Payment({ onBackToChat }) {
  const [amount, setAmount] = useState(1000); // $10.00 in cents
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    // Check if returning from Stripe checkout
    const urlParams = new URLSearchParams(window.location.search);
    const paymentStatus = urlParams.get('payment');
    const sessionId = urlParams.get('session_id');

    if (paymentStatus === 'success' && sessionId) {
      confirmPayment(sessionId);
    } else if (paymentStatus === 'cancel') {
      setMessage("Payment cancelled");
    }
  }, []);

  const confirmPayment = async (sessionId) => {
    try {
      setLoading(true);
      const res = await axios.post(`${API_URL}/api/payment/confirm`, {
        sessionId: sessionId
      });

      if (res.data.status === 'success') {
        setMessage(`✅ Payment successful! Amount: $${res.data.amount}`);
        // Clear URL parameters
        window.history.replaceState({}, document.title, window.location.pathname);
      } else {
        setMessage(`Payment status: ${res.data.paymentStatus}`);
      }
    } catch (error) {
      console.error("Error confirming payment:", error);
      setMessage("❌ Error confirming payment");
    } finally {
      setLoading(false);
    }
  };

  const handlePayment = async () => {
    try {
      setLoading(true);
      setMessage("");

      const res = await axios.post(`${API_URL}/api/payment/create-checkout-session`, {
        amount: amount,
        currency: "usd",
        userId: "123"
      });

      // Redirect to Stripe checkout
      window.location.href = res.data.url;
    } catch (error) {
      console.error("Error creating checkout session:", error);
      setMessage("❌ Error: " + (error.response?.data?.detail || "Could not create checkout session"));
      setLoading(false);
    }
  };

  return (
    <div className="payment-container">
      <div className="payment-header">
        <h1>💳 Payment</h1>
        {onBackToChat && (
          <button onClick={onBackToChat} className="back-btn">
            ← Back to Chat
          </button>
        )}
      </div>

      <div className="payment-content">
        <div className="payment-card">
          <h2>Subscribe to AI Agent</h2>
          <p>Get unlimited access to all AI agents</p>

          <div className="amount-selector">
            <label>Select Amount:</label>
            <select value={amount} onChange={(e) => setAmount(Number(e.target.value))}>
              <option value={500}>$5.00</option>
              <option value={1000}>$10.00</option>
              <option value={2000}>$20.00</option>
              <option value={5000}>$50.00</option>
            </select>
          </div>

          <button 
            className="payment-btn" 
            onClick={handlePayment}
            disabled={loading}
          >
            {loading ? "Processing..." : `Pay $${(amount / 100).toFixed(2)}`}
          </button>

          {message && (
            <div className={`payment-message ${message.includes('✅') ? 'success' : message.includes('❌') ? 'error' : 'info'}`}>
              {message}
            </div>
          )}

          <div className="payment-info">
            <p>💡 <strong>Test Mode:</strong> Use Stripe test card</p>
            <p>Card: <code>4242 4242 4242 4242</code></p>
            <p>Expiry: Any future date | CVC: Any 3 digits</p>
          </div>
        </div>
      </div>
    </div>
  );
}
