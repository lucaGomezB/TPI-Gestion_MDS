import { Link } from 'react-router-dom';

interface RedirectLink {
  label: string;
  path: string;
}

interface RedirectPageProps {
  title: string;
  description: string;
  links: RedirectLink[];
}

function RedirectPage({ title, description, links }: RedirectPageProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <svg
        className="w-16 h-16 text-[#64748B]/30 mb-4"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={1}
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M9 6.75V15m6-6v8.25m.503 3.498l4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934c-.317.159-.69.159-1.006 0L9.503 3.252a1.125 1.125 0 00-1.006 0L3.622 5.689C3.24 5.88 3 6.27 3 6.695V19.18c0 .836.88 1.38 1.628 1.006l3.869-1.934c.317-.159.69-.159 1.006 0l4.994 2.497c.317.158.69.158 1.006 0z"
        />
      </svg>
      <h3 className="font-serif text-xl text-[#0F172A] mb-1">{title}</h3>
      <p className="text-base text-[#64748B] mb-6 max-w-md">{description}</p>
      {links.length > 0 && (
        <div className="flex flex-wrap gap-3 justify-center">
          {links.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              className="inline-flex items-center justify-center rounded font-medium transition-colors px-6 py-3 text-sm font-medium text-white bg-[#0F172A] hover:bg-[#0F172A]/90"
            >
              {link.label}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

export default RedirectPage;
