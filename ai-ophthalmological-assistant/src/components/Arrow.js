function Arrow() {
  return (
    <div className="arrowWork">
    <svg width="100" height="100" viewBox="0 0 100 100">
      <path
        d="M10 50 L70 50 L50 30 M70 50 L50 70"
        stroke="black"
        strokeWidth="4"
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
    </div>
  );
}

export default Arrow;