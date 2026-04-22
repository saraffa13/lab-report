import { HTMLAttributes } from "react";

interface IconProps extends HTMLAttributes<HTMLSpanElement> {
  name: string;
  filled?: boolean;
  size?: number;
}

export function Icon({ name, filled, size = 20, className = "", style, ...rest }: IconProps) {
  return (
    <span
      className={`material-symbols-outlined ${filled ? "fill-icon" : ""} ${className}`}
      style={{ fontSize: size, ...style }}
      aria-hidden="true"
      {...rest}
    >
      {name}
    </span>
  );
}
