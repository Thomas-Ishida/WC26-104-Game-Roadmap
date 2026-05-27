import { formatTeam, teamFlag } from "../lib/flags";

interface Props {
  name: string;
  className?: string;
  /** Show flag only (no text). */
  flagOnly?: boolean;
}

export function TeamName({ name, className, flagOnly }: Props) {
  if (flagOnly) {
    const flag = teamFlag(name);
    return flag ? (
      <span className={className} title={name} aria-label={name}>
        {flag}
      </span>
    ) : (
      <span className={className}>{name}</span>
    );
  }
  return <span className={className}>{formatTeam(name)}</span>;
}
