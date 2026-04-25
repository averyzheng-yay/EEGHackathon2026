// API Client for OLAPIS Backend
import type {
  User,
  AuthResponse,
  Paper,
  PaperCard,
  DiscussionPost,
  Comment,
  VoteState,
  PaginatedResponse,
  ExpertiseLevel,
  TechnicalLevel,
  AskAIMessage,
} from "./types"

// Reads NEXT_PUBLIC_API_URL from .env.local (includes the /api prefix)
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"

// ── Helpers ───────────────────────────────────────────────────────────────────

function getAuthHeaders(): HeadersInit {
  if (typeof window === "undefined") return {}
  const token = localStorage.getItem("access_token")
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function getSessionId(): string {
  if (typeof window === "undefined") return ""
  let id = sessionStorage.getItem("session_id")
  if (!id) {
    id = crypto.randomUUID()
    sessionStorage.setItem("session_id", id)
  }
  return id
}

async function fetchAPI<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...getAuthHeaders(),
    ...options.headers,
  }
  const response = await fetch(`${API_BASE_URL}${endpoint}`, { ...options, headers })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "An error occurred" }))
    throw new Error(error.detail || `HTTP error ${response.status}`)
  }
  // 204 No Content — return empty object so callers don't crash
  if (response.status === 204) return {} as T
  return response.json()
}

// Convert "Artificial Intelligence" → "artificial-intelligence" for backend slugs
function toSlug(label: string): string {
  return label.toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, "")
}

// ── Shape transformers ────────────────────────────────────────────────────────
// All backend→frontend mapping lives here so no page components need to change.

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function transformUser(raw: any): User {
  return {
    id: raw.id,
    email: raw.email,
    username: raw.username,
    expertise_level: raw.expertise_level,
    onboarding_complete: raw.onboarding_complete ?? false,
    // Backend returns [{tag_slug, priority}]; frontend expects string[]
    interests: (raw.interests || []).map((i: { tag_slug: string } | string) =>
      typeof i === "string" ? i : i.tag_slug
    ),
    created_at: raw.created_at,
    updated_at: raw.updated_at ?? raw.created_at,
  }
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function transformAuthResponse(raw: any): AuthResponse {
  return {
    access_token: raw.access_token,
    refresh_token: raw.refresh_token,
    token_type: raw.token_type,
    user: transformUser(raw.user),
  }
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function transformPaperCard(raw: any): PaperCard {
  return {
    id: raw.id,
    arxiv_id: raw.arxiv_id,
    title: raw.title,
    authors: raw.authors || [],
    year: raw.year ?? null,
    tags: raw.tags || [],
    primary_category: raw.primary_category ?? null,
    upvote_count: raw.upvote_count ?? 0,
    downvote_count: raw.downvote_count ?? 0,
    plain_summary: raw.plain_summary ?? null,
    technical_summary: raw.technical_summary ?? null,
    // summary_preview: prefer plain for general audiences; fall back to technical
    summary_preview: raw.plain_summary || raw.technical_summary || "",
    arxiv_url: raw.arxiv_url ?? null,
  }
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function transformPost(raw: any): DiscussionPost {
  return {
    id: raw.id,
    title: raw.title,
    content: raw.body ?? raw.content ?? "",  // backend uses 'body'
    author: raw.author ?? { id: "", username: "[deleted]" },
    created_at: raw.created_at,
    tags: raw.tags || [],
    technical_level: raw.technical_level,
    upvote_count: raw.upvote_count ?? 0,
    downvote_count: raw.downvote_count ?? 0,
    comment_count: raw.comment_count ?? 0,
    linked_paper: raw.linked_paper
      ? {
          id: raw.linked_paper.id,
          arxiv_id: raw.linked_paper.arxiv_id,
          title: raw.linked_paper.title,
          authors: raw.linked_paper.authors || [],
        }
      : null,
  }
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function transformComment(raw: any): Comment {
  return {
    id: raw.id,
    content: raw.body ?? raw.content ?? "",  // backend uses 'body'
    author: raw.author ?? { id: "", username: "[deleted]" },
    created_at: raw.created_at,
    upvote_count: 0,    // comment voting not yet implemented in backend
    downvote_count: 0,
  }
}

function paginate<T>(items: T[]): PaginatedResponse<T> {
  return { items, cursor: null, has_more: false }
}

// ── AUTH ──────────────────────────────────────────────────────────────────────

export async function login(email: string, password: string): Promise<AuthResponse> {
  const raw = await fetchAPI<AuthResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password, session_id: getSessionId() }),
  })
  const result = transformAuthResponse(raw)
  if (typeof window !== "undefined") {
    localStorage.setItem("access_token", result.access_token)
    localStorage.setItem("refresh_token", result.refresh_token)
  }
  return result
}

export async function signup(
  email: string,
  username: string,
  password: string
): Promise<AuthResponse> {
  // Backend endpoint is /auth/register, not /auth/signup
  const raw = await fetchAPI<AuthResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, username, password }),
  })
  const result = transformAuthResponse(raw)
  if (typeof window !== "undefined") {
    localStorage.setItem("access_token", result.access_token)
    localStorage.setItem("refresh_token", result.refresh_token)
  }
  return result
}

export async function completeOnboarding(
  interests: string[],
  expertise_level: ExpertiseLevel
): Promise<User> {
  // Frontend passes human-readable labels ("Artificial Intelligence");
  // backend expects slugs ("artificial-intelligence").
  const slugs = interests.map(toSlug)
  const raw = await fetchAPI<User>("/users/me/onboarding", {
    method: "POST",
    body: JSON.stringify({ interests: slugs, expertise_level }),
  })
  return transformUser(raw)
}

export async function getCurrentUser(): Promise<User | null> {
  try {
    const raw = await fetchAPI<User>("/users/me")  // was /auth/me
    return transformUser(raw)
  } catch {
    return null
  }
}

export async function logout(): Promise<void> {
  if (typeof window !== "undefined") {
    const refreshToken = localStorage.getItem("refresh_token")
    if (refreshToken) {
      fetchAPI("/auth/logout", {
        method: "POST",
        body: JSON.stringify({ refresh_token: refreshToken }),
      }).catch(() => {}) // best-effort
    }
    localStorage.removeItem("access_token")
    localStorage.removeItem("refresh_token")
  }
}

export async function refreshToken(): Promise<AuthResponse> {
  const token = typeof window !== "undefined" ? localStorage.getItem("refresh_token") : null
  if (!token) throw new Error("No refresh token")
  const raw = await fetchAPI<AuthResponse>("/auth/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token: token }),
  })
  if (typeof window !== "undefined") {
    localStorage.setItem("access_token", raw.access_token)
    localStorage.setItem("refresh_token", raw.refresh_token)
  }
  return raw
}

// ── PAPERS ────────────────────────────────────────────────────────────────────

export async function getPapersFeed(cursor?: string): Promise<PaginatedResponse<PaperCard>> {
  const params = new URLSearchParams()
  if (cursor) params.set("cursor", cursor)
  // Backend endpoint is /papers, not /papers/feed
  const raw = await fetchAPI<{ items: PaperCard[]; next_cursor: string | null; has_more: boolean }>(
    `/papers?${params}`
  )
  return {
    items: (raw.items || []).map(transformPaperCard),
    cursor: raw.next_cursor ?? null,  // backend returns next_cursor, frontend expects cursor
    has_more: raw.has_more,
  }
}

export async function getPaper(id: string): Promise<Paper> {
  return fetchAPI<Paper>(`/papers/${id}`)
}

export async function votePaper(
  id: string,
  vote: "upvote" | "downvote"
): Promise<VoteState> {
  // Backend expects { vote_type: "up" | "down" }, not { vote: "upvote" | "downvote" }
  const vote_type = vote === "upvote" ? "up" : "down"
  return fetchAPI<VoteState>(`/papers/${id}/vote`, {
    method: "POST",
    body: JSON.stringify({ vote_type, session_id: getSessionId() }),
  })
}

// Backend has no DELETE vote endpoint — sending the same vote_type again toggles it off
export async function removeVotePaper(
  id: string,
  currentVote: "upvote" | "downvote"
): Promise<VoteState> {
  const vote_type = currentVote === "upvote" ? "up" : "down"
  return fetchAPI<VoteState>(`/papers/${id}/vote`, {
    method: "POST",
    body: JSON.stringify({ vote_type, session_id: getSessionId() }),
  })
}

// ── DISCUSSION POSTS ──────────────────────────────────────────────────────────

async function _fetchPostsFeed(cursor?: string): Promise<PaginatedResponse<DiscussionPost>> {
  const params = new URLSearchParams()
  if (cursor) params.set("cursor", cursor)
  // Backend endpoint is /posts (not /posts/feed or /feed)
  const raw = await fetchAPI<{ items: DiscussionPost[]; next_cursor: string | null; has_more: boolean }>(
    `/posts?${params}`
  )
  return {
    items: (raw.items || []).map(transformPost),
    cursor: raw.next_cursor ?? null,
    has_more: raw.has_more,
  }
}

export async function getDiscussionsFeed(cursor?: string): Promise<PaginatedResponse<DiscussionPost>> {
  return _fetchPostsFeed(cursor)
}

export async function getHomeFeed(cursor?: string): Promise<PaginatedResponse<DiscussionPost>> {
  return _fetchPostsFeed(cursor)
}

export async function getDiscussionPost(id: string): Promise<DiscussionPost> {
  const raw = await fetchAPI<DiscussionPost>(`/posts/${id}`)
  return transformPost(raw)
}

export async function createPost(data: {
  title: string
  content: string         // frontend calls it content; backend wants body
  tags: string[]
  technical_level: TechnicalLevel
  linked_paper_id?: string // frontend calls it linked_paper_id; backend wants paper_id
}): Promise<DiscussionPost> {
  const raw = await fetchAPI<DiscussionPost>("/posts", {
    method: "POST",
    body: JSON.stringify({
      title: data.title,
      body: data.content,             // content → body
      tags: data.tags,
      technical_level: data.technical_level,
      paper_id: data.linked_paper_id ?? null,  // linked_paper_id → paper_id
    }),
  })
  return transformPost(raw)
}

export async function votePost(
  id: string,
  vote: "upvote" | "downvote"
): Promise<VoteState> {
  const vote_type = vote === "upvote" ? "up" : "down"
  return fetchAPI<VoteState>(`/posts/${id}/vote`, {
    method: "POST",
    body: JSON.stringify({ vote_type, session_id: getSessionId() }),
  })
}

export async function removeVotePost(
  id: string,
  currentVote: "upvote" | "downvote"
): Promise<VoteState> {
  const vote_type = currentVote === "upvote" ? "up" : "down"
  return fetchAPI<VoteState>(`/posts/${id}/vote`, {
    method: "POST",
    body: JSON.stringify({ vote_type, session_id: getSessionId() }),
  })
}

// ── COMMENTS ─────────────────────────────────────────────────────────────────

// Backend returns a plain array (not paginated); we wrap it for SWRInfinite compatibility.
export async function getComments(
  postId: string,
  _cursor?: string
): Promise<PaginatedResponse<Comment>> {
  const raw = await fetchAPI<Comment[]>(`/posts/${postId}/comments`)
  return paginate((raw || []).map(transformComment))
}

export async function createComment(postId: string, content: string): Promise<Comment> {
  const raw = await fetchAPI<Comment>(`/posts/${postId}/comments`, {
    method: "POST",
    body: JSON.stringify({ body: content }),  // frontend content → backend body
  })
  return transformComment(raw)
}

// Comment voting is not yet implemented in the backend — stub so the UI doesn't break
export async function voteComment(
  _commentId: string,
  vote: "upvote" | "downvote"
): Promise<VoteState> {
  return { user_vote: vote, upvote_count: 0, downvote_count: 0 }
}

// ── SEARCH ────────────────────────────────────────────────────────────────────
// Backend has a unified /search endpoint that returns both papers and posts.

export async function searchPapers(
  query: string,
  tags?: string[],
  _cursor?: string
): Promise<PaginatedResponse<PaperCard>> {
  const params = new URLSearchParams()
  params.set("q", query)
  if (tags?.length) params.set("tag", tags[0])
  const raw = await fetchAPI<{
    papers: PaperCard[]
    papers_next_cursor: string | null
  }>(`/search?${params}`)
  return {
    items: (raw.papers || []).map(transformPaperCard),
    cursor: raw.papers_next_cursor ?? null,
    has_more: !!raw.papers_next_cursor,
  }
}

export async function searchPosts(
  query: string,
  tags?: string[],
  _cursor?: string
): Promise<PaginatedResponse<DiscussionPost>> {
  const params = new URLSearchParams()
  params.set("q", query)
  if (tags?.length) params.set("tag", tags[0])
  const raw = await fetchAPI<{
    posts: DiscussionPost[]
    posts_next_cursor: string | null
  }>(`/search?${params}`)
  return {
    items: (raw.posts || []).map(transformPost),
    cursor: raw.posts_next_cursor ?? null,
    has_more: !!raw.posts_next_cursor,
  }
}

// ── ASK AI ────────────────────────────────────────────────────────────────────

export async function askAI(
  paperId: string,
  messages: AskAIMessage[]
): Promise<AskAIMessage> {
  // Backend expects { message: string, history: [{role, content}] }
  const lastMessage = messages[messages.length - 1]
  const history = messages.slice(0, -1)
  const raw = await fetchAPI<{ response: string }>(`/ask-ai/${paperId}/chat`, {
    method: "POST",
    body: JSON.stringify({
      message: lastMessage.content,
      history: history.map((m) => ({ role: m.role, content: m.content })),
    }),
  })
  return { role: "assistant", content: raw.response }
}

// ── USER SETTINGS ─────────────────────────────────────────────────────────────

export async function updateUserSettings(data: {
  interests?: string[]
  expertise_level?: ExpertiseLevel
}): Promise<User> {
  const raw = await fetchAPI<User>("/users/me", {
    method: "PATCH",
    body: JSON.stringify({
      ...data,
      // interests may be slugs (from settings) or labels (from elsewhere) — normalise both
      interests: data.interests?.map(toSlug),
    }),
  })
  return transformUser(raw)
}
