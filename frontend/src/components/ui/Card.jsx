function Card({ children, className = '' }) {
  return (
    <section className={`rounded-lg border border-slate-800 bg-slate-900 ${className}`}>
      {children}
    </section>
  );
}

export default Card;
