// API Types for OLAPIS - Reddit for Research

// User types
export type ExpertiseLevel = "beginner" | "intermediate" | "expert"

export interface User {
  id: string
  email: string
  username: string
  expertise_level: ExpertiseLevel
  interests: string[]          // tag slugs, e.g. ["artificial-intelligence", "machine-learning"]
  onboarding_complete: boolean
  created_at: string
  updated_at: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

// Paper types
export interface Paper {
  id: string
  arxiv_id: string
  title: string
  authors: string[]
  year: number
  abstract: string
  plain_summary: string | null
  technical_summary: string | null
  tags: string[]
  primary_category: string | null
  upvote_count: number
  downvote_count: number
  view_count: number
  ingested_at: string
  published_at: string | null
  arxiv_url: string | null
  linked_posts?: LinkedPost[]
}

export interface LinkedPost {
  id: string
  title: string
  author_username: string | null
  comment_count: number
  upvote_count: number
}

export interface PaperCard {
  id: string
  arxiv_id: string
  title: string
  authors: string[]
  year: number | null
  tags: string[]
  primary_category: string | null
  upvote_count: number
  downvote_count: number
  // Both summary fields are present; paper-card uses summary_preview as display text
  plain_summary: string | null
  technical_summary: string | null
  summary_preview: string      // derived: plain_summary ?? technical_summary ?? ""
  arxiv_url: string | null
}

// Discussion Post types
export type TechnicalLevel = "beginner" | "intermediate" | "expert"

export interface DiscussionPost {
  id: string
  title: string
  content: string              // mapped from backend's `body` field
  author: {
    id: string
    username: string
  }
  created_at: string
  tags: string[]
  technical_level: TechnicalLevel
  upvote_count: number
  downvote_count: number
  comment_count: number
  linked_paper?: {
    id: string
    arxiv_id: string
    title: string
    authors: string[]          // may be empty [] if not returned by this endpoint
  } | null
}

export interface Comment {
  id: string
  content: string              // mapped from backend's `body` field
  author: {
    id: string
    username: string
  }
  created_at: string
  upvote_count: number         // always 0 — comment voting not yet implemented in backend
  downvote_count: number
}

// Vote types
export type VoteType = "upvote" | "downvote" | null

export interface VoteState {
  user_vote: VoteType
  upvote_count: number
  downvote_count: number
}

// Pagination — cursor field matches backend's next_cursor (transformed in api.ts)
export interface PaginatedResponse<T> {
  items: T[]
  cursor: string | null
  has_more: boolean
}

// Search types
export interface SearchResults {
  papers: PaginatedResponse<PaperCard>
  posts: PaginatedResponse<DiscussionPost>
}

// Ask AI types
export interface AskAIMessage {
  role: "user" | "assistant"
  content: string
}

// Topic/Tag taxonomy — display labels for the onboarding UI
// These are human-readable; api.ts slugifies them before sending to the backend.
export const TOPIC_CATEGORIES = {
  "Computer Science": [
    "Artificial Intelligence",
    "Machine Learning",
    "Computer Vision",
    "Natural Language Processing",
    "Robotics",
    "Cryptography",
    "Databases",
    "Distributed Computing",
    "Human-Computer Interaction",
    "Software Engineering",
  ],
  "Mathematics": [
    "Algebra",
    "Analysis",
    "Combinatorics",
    "Geometry",
    "Logic",
    "Number Theory",
    "Probability",
    "Statistics",
    "Topology",
    "Applied Mathematics",
  ],
  "Physics": [
    "Astrophysics",
    "Condensed Matter",
    "High Energy Physics",
    "Nuclear Physics",
    "Optics",
    "Quantum Computing",
    "General Relativity",
    "Statistical Mechanics",
    "Plasma Physics",
    "Fluid Dynamics",
  ],
  "Biology": [
    "Bioinformatics",
    "Cell Biology",
    "Ecology",
    "Genetics",
    "Genomics",
    "Microbiology",
    "Neuroscience",
    "Structural Biology",
    "Systems Biology",
    "Evolutionary Biology",
  ],
  "Chemistry": [
    "Analytical Chemistry",
    "Biochemistry",
    "Chemical Physics",
    "Inorganic Chemistry",
    "Materials Science",
    "Organic Chemistry",
    "Physical Chemistry",
    "Polymer Science",
    "Computational Chemistry",
    "Environmental Chemistry",
  ],
  "Economics & Finance": [
    "Econometrics",
    "Economic Theory",
    "Finance",
    "Game Theory",
    "Quantitative Finance",
    "Behavioral Economics",
  ],
} as const

export const ALL_TOPICS = Object.entries(TOPIC_CATEGORIES).flatMap(
  ([category, topics]) => topics.map((topic) => ({ category, topic }))
)

export const QUICK_FILTER_TOPICS = [
  "AI",
  "Math",
  "Physics",
  "Biology",
  "Chemistry",
  "Economics",
] as const
