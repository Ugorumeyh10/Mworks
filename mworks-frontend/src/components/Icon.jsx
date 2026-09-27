export default function Icon({ name, className = '', size }) {
  const style = size ? { width: size, height: size } : undefined;
  return (
    <svg className={`icon ${className}`} style={style}>
      <use href={`#i-${name}`} />
    </svg>
  );
}
