# 🚀 Secure Django E-Commerce Payment Gateway with Stripe & Webhooks

A production-ready payment integration system built with **Django**, **Django REST Framework (DRF)**, and **Stripe SDK**. This system handles complex checkout lifecycles, secure webhook validation, and displays a dynamic real-time customer dashboard.

---

## 🔑 Key Features

* 🔒 **Secure Stripe Integration:** Uses Stripe Elements to securely process payments without handling sensitive card data on the server (PCI Compliant).
* 🛡️ **3D Secure (SCA) Ready:** Handles multi-factor authentication (like 3D Secure 2) seamlessly during the checkout flow.
* ⚡ **Robust Webhook Processor:** An engineered webhook receiver that securely validates Stripe signatures to prevent spoofing and replays, managing events like `payment_intent.succeeded`, `payment_intent.payment_failed`, and `payment_intent.canceled`.
* 📊 **Interactive Customer Dashboard:** A clean, responsive Tailwind-CSS dashboard displaying order history, dynamic payment badges, and instant redirection after payment.
* 📉 **Inventory & Cart Auto-Sync:** Automatically updates product stock levels and empties the user's cart strictly upon successful payment confirmation.

---

## 🛠️ Tech Stack

* **Backend:** Python / Django / Django REST Framework
* **Frontend:** Tailwind CSS (via CDN) / JavaScript (Stripe.js v3)
* **Payment Processing:** Stripe API
* **Configuration:** Python-environ (for securely handling secret keys)

---

## 🚀 Quick Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd <repository-folder>