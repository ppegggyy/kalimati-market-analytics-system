import '../styles/components.css';

export function Card({ title, children }) {
  return (
    <div className="card">
      {title && <h2 className="card-title">{title}</h2>}
      {children}
    </div>
  );
}
