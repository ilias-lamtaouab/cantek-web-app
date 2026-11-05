interface ServiceIconProps {
  icon: string | null;
  size?: number;
}

const ICONS: Record<string, React.ReactNode> = {
  code: (
    <>
      <polyline points="16 18 22 12 16 6" />
      <polyline points="8 6 2 12 8 18" />
    </>
  ),
  ai: (
    <>
      <rect x="5" y="5" width="14" height="14" rx="2" />
      <rect x="9" y="9" width="6" height="6" rx="1" />
      <line x1="9" y1="1" x2="9" y2="5" />
      <line x1="15" y1="1" x2="15" y2="5" />
      <line x1="9" y1="19" x2="9" y2="23" />
      <line x1="15" y1="19" x2="15" y2="23" />
      <line x1="1" y1="9" x2="5" y2="9" />
      <line x1="1" y1="15" x2="5" y2="15" />
      <line x1="19" y1="9" x2="23" y2="9" />
      <line x1="19" y1="15" x2="23" y2="15" />
    </>
  ),
  cloud: <path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z" />,
  shield: <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />,
  globe: (
    <>
      <circle cx="12" cy="12" r="10" />
      <line x1="2" y1="12" x2="22" y2="12" />
      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
    </>
  ),
  tool: (
    <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
  ),
  zap: <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />,
  phone: (
    <>
      <rect x="5" y="2" width="14" height="20" rx="2" />
      <line x1="12" y1="18" x2="12.01" y2="18" />
    </>
  ),
  database: (
    <>
      <ellipse cx="12" cy="5" rx="9" ry="3" />
      <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
      <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
    </>
  ),
};

const EMOJI_TO_ICON: Record<string, string> = {
  "💻": "code",
  "🖥": "code",
  "⌨": "code",
  "🧠": "ai",
  "🤖": "ai",
  "🔮": "ai",
  "☁": "cloud",
  "🔒": "shield",
  "🔐": "shield",
  "🛡": "shield",
  "🌐": "globe",
  "🔧": "tool",
  "🛠": "tool",
  "⚙": "tool",
  "💡": "zap",
  "⚡": "zap",
  "🚀": "zap",
  "📱": "phone",
  "🗄": "database",
  "💾": "database",
};

function ServiceIcon({ icon, size = 26 }: ServiceIconProps) {
  const base = (icon || "").trim().replace(/\uFE0F/g, "");
  const lower = base.toLowerCase();
  const name = ICONS[lower] ? lower : EMOJI_TO_ICON[base] || "zap";

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {ICONS[name]}
    </svg>
  );
}

export default ServiceIcon;