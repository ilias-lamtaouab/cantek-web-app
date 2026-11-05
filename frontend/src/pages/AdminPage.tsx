import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { isAxiosError } from "axios";
import ProductCard from "../components/ProductCard";
import ProductForm from "../components/ProductForm";
import AuthForm from "../components/AuthForm";
import ThemeToggle from "../components/ThemeToggle";
import QuotesPanel from "../components/QuotesPanel";
import type { Quote } from "../components/QuotesPanel";
import api from "../api";

interface Product {
  id: number;
  name: string;
  description: string | null;
  price: number;
  discount_percent: number;
  photo_url: string | null;
  name_fr: string | null;
  description_fr: string | null;
  quote_only: boolean;
}

interface ContactMessage {
  id: number;
  name: string;
  email: string;
  message: string;
  reply: string | null;
  replied_at: string | null;
}

interface Order {
  id: number;
  client_name: string;
  client_email: string;
  product_id: number | null;
  service_name: string;
  unit_price: number;
  discount_percent: number;
  total_price: number;
  note: string | null;
  status: string;
  created_at: string;
  confirmed_at: string | null;
}

type Panel = "dashboard" | "services" | "orders" | "messages" | "quotes";

function AdminPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState<string | null>(localStorage.getItem("token"));
  const [showForm, setShowForm] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [messages, setMessages] = useState<ContactMessage[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [panel, setPanel] = useState<Panel>("dashboard");
  const [highlightedOrderId, setHighlightedOrderId] = useState<number | null>(null);
  const [replyTexts, setReplyTexts] = useState<Record<number, string>>({});
  const [sendingId, setSendingId] = useState<number | null>(null);
  const [replyError, setReplyError] = useState<{ id: number; text: string } | null>(null);
  const [confirmingId, setConfirmingId] = useState<number | null>(null);
  const [orderError, setOrderError] = useState<{ id: number; text: string } | null>(null);

  const pendingCount = orders.filter((order) => order.status === "pending").length;
  const pendingQuoteCount = quotes.filter((quote) => quote.status === "pending").length;

  // ---- Dashboard numbers (computed here from the orders we already have) ----
  const confirmedOrders = orders.filter((order) => order.status === "confirmed");
  const totalRevenue = confirmedOrders.reduce((sum, order) => sum + order.total_price, 0);

  const monthlyData = (() => {
    const now = new Date();
    const months: { key: string; label: string; revenue: number; count: number }[] = [];
    for (let i = 5; i >= 0; i--) {
      const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
      months.push({
        key: `${d.getFullYear()}-${d.getMonth()}`,
        label: d.toLocaleDateString("en-US", { month: "short" }),
        revenue: 0,
        count: 0,
      });
    }
    confirmedOrders.forEach((order) => {
      const when = new Date((order.confirmed_at || order.created_at) + "Z");
      const key = `${when.getFullYear()}-${when.getMonth()}`;
      const month = months.find((m) => m.key === key);
      if (month) {
        month.revenue += order.total_price;
        month.count += 1;
      }
    });
    return months;
  })();

  const sixMonthRevenue = monthlyData.reduce((sum, m) => sum + m.revenue, 0);
  const averagePerMonth = sixMonthRevenue / 6;
  const maxMonthRevenue = Math.max(...monthlyData.map((m) => m.revenue), 0);

  const bestSeller = (() => {
    const counts: Record<string, { name: string; count: number }> = {};
    confirmedOrders.forEach((order) => {
      const key = order.product_id !== null ? `p${order.product_id}` : order.service_name;
      if (!counts[key]) counts[key] = { name: order.service_name, count: 0 };
      counts[key].count += 1;
    });
    const list = Object.values(counts).sort((a, b) => b.count - a.count);
    return list.length > 0 ? list[0] : null;
  })();

  const fetchProducts = () => {
    api
      .get<Product[]>("/products")
      .then((response) => setProducts(response.data))
      .catch((error) => console.error("Failed to fetch products:", error))
      .finally(() => setLoading(false));
  };

  const fetchMessages = () => {
    api
      .get<ContactMessage[]>("/contact", {
        headers: { Authorization: `Bearer ${token}` },
      })
      .then((response) => setMessages(response.data))
      .catch((error) => console.error("Failed to fetch messages:", error));
  };

  const fetchOrders = () => {
    api
      .get<Order[]>("/orders", {
        headers: { Authorization: `Bearer ${token}` },
      })
      .then((response) => setOrders(response.data))
      .catch((error) => console.error("Failed to fetch orders:", error));
  };

  const fetchQuotes = () => {
    api
      .get<Quote[]>("/quotes", {
        headers: { Authorization: `Bearer ${token}` },
      })
      .then((response) => setQuotes(response.data))
      .catch((error) => console.error("Failed to fetch quotes:", error));
  };

  const handleReplySubmit = async (messageId: number) => {
    const text = (replyTexts[messageId] || "").trim();
    if (!text) return;

    setSendingId(messageId);
    setReplyError(null);
    try {
      await api.put(
        `/contact/${messageId}/reply`,
        { reply: text },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setReplyTexts((prev) => ({ ...prev, [messageId]: "" }));
      fetchMessages();
    } catch (error) {
      console.error("Failed to send reply:", error);
      setReplyError({
        id: messageId,
        text: "Could not send the email. Your text is kept, please try again.",
      });
    } finally {
      setSendingId(null);
    }
  };

  const handleConfirmOrder = async (orderId: number) => {
    const confirmed = window.confirm(
      "Confirm this order? The client will receive an email with a PDF."
    );
    if (!confirmed) return;

    setConfirmingId(orderId);
    setOrderError(null);
    try {
      await api.put(
        `/orders/${orderId}/confirm`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      fetchOrders();
    } catch (error) {
      console.error("Failed to confirm order:", error);
      const detail = isAxiosError(error) ? error.response?.data?.detail : undefined;
      setOrderError({
        id: orderId,
        text:
          typeof detail === "string"
            ? detail
            : "Could not confirm the order. Please try again.",
      });
    } finally {
      setConfirmingId(null);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  useEffect(() => {
    if (!token) return;
    fetchMessages();
    fetchOrders();
    fetchQuotes();
    const interval = setInterval(() => {
      fetchMessages();
      fetchOrders();
      fetchQuotes();
    }, 10000);
    return () => clearInterval(interval);
    // The polling only restarts when the token changes; the fetch functions read the current token.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  // From an accepted quote: open the Orders tab on its order
  const handleShowOrder = (orderId: number) => {
    setPanel("orders");
    setHighlightedOrderId(orderId);
    setTimeout(() => {
      document
        .getElementById(`order-${orderId}`)
        ?.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 50);
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    setToken(null);
  };

  const handleAddClick = () => {
    setEditingProduct(null);
    setShowForm(true);
  };

  const handleEditClick = (product: Product) => {
    setEditingProduct(product);
    setShowForm(true);
  };

  const handleDeleteClick = async (productId: number) => {
    const confirmed = window.confirm("Delete this service?");
    if (!confirmed) return;

    try {
      await api.delete(`/products/${productId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      fetchProducts();
    } catch (error) {
      console.error("Failed to delete product:", error);
    }
  };

  const handleFormSubmit = async (data: {
    name: string;
    description: string;
    price: number;
    discount_percent: number;
    photo_url: string;
    name_fr?: string;
    description_fr?: string;
    quote_only: boolean;
  }) => {
    try {
      if (editingProduct) {
        await api.put(`/products/${editingProduct.id}`, data, {
          headers: { Authorization: `Bearer ${token}` },
        });
      } else {
        await api.post("/products", data, {
          headers: { Authorization: `Bearer ${token}` },
        });
      }
      setShowForm(false);
      fetchProducts();
    } catch (error) {
      console.error("Failed to save product:", error);
    }
  };

  if (!token) {
    return (
      <div className="auth-page">
        <ThemeToggle />
        <Link to="/shop" className="logo-tile" aria-label="Cantek">
          <img src="/logo.png" alt="Cantek" />
        </Link>
        <AuthForm onLoginSuccess={(t) => setToken(t)} />
        <Link to="/shop" className="auth-back">View site</Link>
      </div>
    );
  }

  return (
    <div className="admin-layout">
      <aside className="admin-sidebar">
        <Link to="/shop" className="logo-tile" aria-label="Cantek">
          <img src="/logo.png" alt="Cantek" />
        </Link>

        <nav className="admin-tabs" aria-label="Admin">
          <button
            className={`admin-tab ${panel === "dashboard" ? "active" : ""}`}
            onClick={() => setPanel("dashboard")}
            aria-current={panel === "dashboard" ? "page" : undefined}
          >
            Dashboard
          </button>
          <button
            className={`admin-tab ${panel === "services" ? "active" : ""}`}
            onClick={() => setPanel("services")}
            aria-current={panel === "services" ? "page" : undefined}
          >
            Services
          </button>
          <button
            className={`admin-tab ${panel === "orders" ? "active" : ""}`}
            onClick={() => setPanel("orders")}
            aria-current={panel === "orders" ? "page" : undefined}
          >
            Orders ({pendingCount})
          </button>
          <button
            className={`admin-tab ${panel === "messages" ? "active" : ""}`}
            onClick={() => setPanel("messages")}
            aria-current={panel === "messages" ? "page" : undefined}
          >
            Messages ({messages.length})
          </button>
          <button
            className={`admin-tab ${panel === "quotes" ? "active" : ""}`}
            onClick={() => setPanel("quotes")}
            aria-current={panel === "quotes" ? "page" : undefined}
          >
            Quotes ({pendingQuoteCount})
          </button>
        </nav>

        <div className="admin-sidebar-foot">
          <Link to="/shop" className="nav-link">View site</Link>
          <div className="admin-foot-row">
            <button className="btn btn-outline btn-sm logout-btn" onClick={handleLogout}>Log Out</button>
            <ThemeToggle />
          </div>
        </div>
      </aside>

      <main className="admin-main">
      {panel === "services" && (
        <div className="admin-bar">
          <button className="btn btn-grad add-btn" onClick={handleAddClick}>+ Add Service</button>
        </div>
      )}

      {showForm && (
        <ProductForm
          initialData={
            editingProduct
              ? {
                  name: editingProduct.name,
                  description: editingProduct.description || "",
                  price: editingProduct.price,
                  discount_percent: editingProduct.discount_percent,
                  photo_url: editingProduct.photo_url || "",
                  name_fr: editingProduct.name_fr || "",
                  description_fr: editingProduct.description_fr || "",
                  quote_only: editingProduct.quote_only,
                }
              : undefined
          }
          onSubmit={handleFormSubmit}
          onCancel={() => setShowForm(false)}
        />
      )}

      {panel === "dashboard" && (
        <div className="dashboard">
          <h3>Dashboard</h3>
          <p className="dashboard-note">
            Only confirmed orders count as sales. Months with no sales show as zero.
          </p>

          <div className="stat-grid">
            <div className="stat-card">
              <span className="stat-label">Total revenue</span>
              <span className="stat-value">${totalRevenue.toFixed(2)}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Average per month (last 6)</span>
              <span className="stat-value">${averagePerMonth.toFixed(2)}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Confirmed orders</span>
              <span className="stat-value">{confirmedOrders.length}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Pending orders</span>
              <span className="stat-value">{pendingCount}</span>
            </div>
          </div>

          <div className="chart-card">
            <h4>Revenue per month</h4>
            <div className="bar-chart">
              {monthlyData.map((m) => (
                <div className="bar-col" key={m.key}>
                  <span className="bar-value">
                    {m.revenue > 0 ? `$${m.revenue.toFixed(0)}` : ""}
                  </span>
                  <div className="bar-track">
                    <div
                      className="bar"
                      style={{
                        height: `${maxMonthRevenue > 0 ? (m.revenue / maxMonthRevenue) * 100 : 0}%`,
                      }}
                    />
                  </div>
                  <span className="bar-label">{m.label}</span>
                </div>
              ))}
            </div>
          </div>

          <p className="dashboard-best">
            Best-selling service:{" "}
            <strong>
              {bestSeller ? `${bestSeller.name} (${bestSeller.count})` : "No sales yet"}
            </strong>
          </p>
        </div>
      )}

      {panel === "orders" && (
        <div className="messages-panel">
          <h3>Orders</h3>
          {orders.length === 0 ? (
            <p className="status-text">No orders yet.</p>
          ) : (
            orders.map((order) => (
              <div
                className={`message-card ${highlightedOrderId === order.id ? "order-highlight" : ""}`}
                id={`order-${order.id}`}
                key={order.id}
              >
                <div className="order-card-head">
                  <h4>{order.service_name}</h4>
                  <span className={`status-badge ${order.status === "confirmed" ? "confirmed" : "pending"}`}>
                    {order.status === "confirmed" ? "Confirmed" : "Pending"}
                  </span>
                </div>
                <p className="order-client">
                  {order.client_name} · {order.client_email}
                </p>
                <p>
                  Total: <span className="order-total">${order.total_price.toFixed(2)}</span>
                  {order.discount_percent > 0 && ` (${order.discount_percent}% discount)`}
                </p>
                {order.note && <p>Note: {order.note}</p>}

                <div className="order-actions">
                  <span className="order-date">
                    Ordered {new Date(order.created_at + "Z").toLocaleString()}
                  </span>
                  {order.status === "pending" && (
                    <button
                      className="btn btn-grad btn-sm confirm-btn"
                      onClick={() => handleConfirmOrder(order.id)}
                      disabled={confirmingId === order.id}
                    >
                      {confirmingId === order.id ? "Confirming..." : "Confirm order"}
                    </button>
                  )}
                </div>
                {orderError && orderError.id === order.id && (
                  <p className="order-error">{orderError.text}</p>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {panel === "messages" && (
        <div className="messages-panel">
          <h3>Contact Messages</h3>
          {messages.length === 0 ? (
            <p className="status-text">No messages yet.</p>
          ) : (
            messages.map((msg) => (
              <div className="message-card" key={msg.id}>
                <div className="message-header">
                  <strong>{msg.name}</strong>
                  <span>{msg.email}</span>
                </div>
                <p>{msg.message}</p>

                {msg.reply ? (
                  <div className="reply-box replied">
                    <strong>Replied</strong>
                    {msg.replied_at && (
                      <span> · {new Date(msg.replied_at + "Z").toLocaleString()}</span>
                    )}
                    <p>{msg.reply}</p>
                  </div>
                ) : (
                  <div className="reply-box">
                    <textarea
                      className="reply-input"
                      placeholder="Write your reply..."
                      value={replyTexts[msg.id] || ""}
                      onChange={(e) =>
                        setReplyTexts((prev) => ({ ...prev, [msg.id]: e.target.value }))
                      }
                    />
                    {replyError && replyError.id === msg.id && (
                      <p className="reply-error">{replyError.text}</p>
                    )}
                    <button
                      className="btn btn-grad btn-sm reply-btn"
                      onClick={() => handleReplySubmit(msg.id)}
                      disabled={sendingId === msg.id}
                    >
                      {sendingId === msg.id ? "Sending..." : "Send reply"}
                    </button>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {panel === "quotes" && (
        <QuotesPanel
          quotes={quotes}
          token={token}
          onQuotesChanged={fetchQuotes}
          onShowOrder={handleShowOrder}
        />
      )}

      {panel === "services" &&
        (loading ? (
          <p className="status-text">Loading services...</p>
        ) : (
          <div className="product-grid">
            {products.map((product) => (
              <ProductCard
                key={product.id}
                name={product.name}
                description={product.description}
                price={product.price}
                discountPercent={product.discount_percent}
                photoUrl={product.photo_url}
                quoteOnly={product.quote_only}
                isLoggedIn={true}
                onEdit={() => handleEditClick(product)}
                onDelete={() => handleDeleteClick(product.id)}
              />
            ))}
          </div>
        ))}
      </main>
    </div>
  );
}

export default AdminPage;