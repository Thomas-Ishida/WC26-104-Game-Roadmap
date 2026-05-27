/** ISO 3166-1 alpha-2 codes for FIFA team names used in this project. */
const TEAM_ISO: Record<string, string> = {
  Algeria: "DZ",
  Argentina: "AR",
  Australia: "AU",
  Austria: "AT",
  Belgium: "BE",
  "Bosnia and Herzegovina": "BA",
  Brazil: "BR",
  Canada: "CA",
  "Cape Verde": "CV",
  Colombia: "CO",
  Croatia: "HR",
  Curaçao: "CW",
  Czechia: "CZ",
  "Democratic Republic of the Congo": "CD",
  Ecuador: "EC",
  Egypt: "EG",
  France: "FR",
  Germany: "DE",
  Ghana: "GH",
  Haiti: "HT",
  Iran: "IR",
  Iraq: "IQ",
  "Ivory Coast": "CI",
  Japan: "JP",
  Jordan: "JO",
  Mexico: "MX",
  Morocco: "MA",
  Netherlands: "NL",
  "New Zealand": "NZ",
  Norway: "NO",
  Panama: "PA",
  Paraguay: "PY",
  Portugal: "PT",
  Qatar: "QA",
  "Saudi Arabia": "SA",
  Senegal: "SN",
  "South Africa": "ZA",
  "South Korea": "KR",
  Spain: "ES",
  Sweden: "SE",
  Switzerland: "CH",
  Tunisia: "TN",
  Turkey: "TR",
  "United States": "US",
  Uruguay: "UY",
  Uzbekistan: "UZ",
};

/** Subnational / special cases where ISO country flags are misleading. */
const TEAM_FLAG_OVERRIDE: Record<string, string> = {
  England: "\u{1F3F4}\u{E0067}\u{E0062}\u{E0065}\u{E006E}\u{E007F}",
  Scotland: "\u{1F3F4}\u{E0067}\u{E0062}\u{E0073}\u{E0063}\u{E0074}\u{E007F}",
};

const REGIONAL_A = 0x1f1e6;

export function isoToFlag(iso: string): string {
  const code = iso.toUpperCase();
  if (code.length !== 2) return "";
  return [...code]
    .map((c) => {
      const n = c.charCodeAt(0) - 65;
      if (n < 0 || n > 25) return "";
      return String.fromCodePoint(REGIONAL_A + n);
    })
    .join("");
}

/** Flag emoji for a team name, or empty string if unknown. */
export function teamFlag(team: string): string {
  if (TEAM_FLAG_OVERRIDE[team]) return TEAM_FLAG_OVERRIDE[team];
  const iso = TEAM_ISO[team];
  return iso ? isoToFlag(iso) : "";
}

/** e.g. "🇦🇷 Argentina" */
export function formatTeam(team: string): string {
  const flag = teamFlag(team);
  return flag ? `${flag} ${team}` : team;
}
