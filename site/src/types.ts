export interface Team {
  team: string;
  elo: number;
  form: number;
  gd: number;
  squad: number;
  slug: string;
}

export interface Fixture {
  group: string;
  home: string;
  away: string;
  p_home: number;
  p_draw: number;
  p_away: number;
  baseline_p_home?: number | null;
  baseline_p_draw?: number | null;
  baseline_p_away?: number | null;
}

export interface GroupStandingRow {
  rank: number;
  team: string;
  pts: number;
  gd: number;
  gf: number;
  w: number;
  d: number;
  l: number;
  elo: number;
}

export interface GroupBlock {
  group: string;
  standings: GroupStandingRow[];
}

export interface MatchupProb {
  home: string;
  away: string;
  p_home: number;
  p_draw: number;
  p_away: number;
}

export interface MatrixEntry {
  home: string;
  away: string;
  p_home: number;
  p_draw: number;
  p_away: number;
}

export interface ChampionOdds {
  team: string;
  p: number;
  source: string;
  n_sims: number;
  ci_low?: number;
  ci_high?: number;
  wins?: number;
}

export interface BracketMatch {
  id: number;
  team_a: string;
  team_b: string;
  winner: string;
  p_win_a: number;
  p_win_b: number;
}

export interface BracketRound {
  round: string;
  matches: BracketMatch[];
}

export interface BracketTree {
  rounds: BracketRound[];
  champion: string;
}

export interface ModelMetric {
  notebook: string;
  model: string;
  accuracy: number;
  split: string;
  f1_macro?: number;
  f1_draw?: number;
  tier?: "primary" | "exploratory";
  role?: string;
  note?: string;
  n_test?: number;
}

export interface MethodologyData {
  what_this_is: string[];
  limitations: string[];
  design_choices: string[];
}

export interface Findings {
  home_win_pct: number;
  draw_pct: number;
  away_win_pct: number;
  squad_top10: { team: string; squad_quality: number }[];
  chalk_champion: string;
  notes: string[];
}

export interface SiteData {
  teams: Team[];
  fixtures: Fixture[];
  matchups: MatchupProb[];
  matchupMatrix: MatrixEntry[];
  championOdds: ChampionOdds[];
  chalkBracket: BracketTree;
  modelMetrics: ModelMetric[];
  findings: Findings;
  defaultGroups: GroupBlock[];
  methodology: MethodologyData;
}
