// API Types for OLAPIS - Reddit for Research

// User types
export type ExpertiseLevel = "beginner" | "intermediate" | "expert"

export interface User {
  id: string
  email: string
  username: string
  expertise_level: ExpertiseLevel
  interests: string[]
  created_at: string
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
  plain_summary: string
  technical_summary: string
  tags: string[]
  upvote_count: number
  downvote_count: number
  ingested_at: string
  arxiv_url: string
}

export interface PaperCard {
  id: string
  arxiv_id: string
  title: string
  authors: string[]
  year: number
  tags: string[]
  upvote_count: number
  downvote_count: number
  summary_preview: string
}

// Discussion Post types
export type TechnicalLevel = "beginner" | "intermediate" | "expert"

export interface DiscussionPost {
  id: string
  title: string
  content: string
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
  linked_paper?: PaperCard | null
}

export interface Comment {
  id: string
  content: string
  author: {
    id: string
    username: string
  }
  created_at: string
  upvote_count: number
  downvote_count: number
}

// Vote types
export type VoteType = "upvote" | "downvote" | null

export interface VoteState {
  user_vote: VoteType
  upvote_count: number
  downvote_count: number
}

// Pagination
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

// Topic/Tag taxonomy
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
    "Quantum Physics",
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
