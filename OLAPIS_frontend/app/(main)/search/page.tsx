"use client"

import { useSearchParams, useRouter } from "next/navigation"
import { useState, useEffect, useCallback, Suspense } from "react"
import useSWR from "swr"
import { Search, RefreshCw } from "lucide-react"
import { toast } from "sonner"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Skeleton } from "@/components/ui/skeleton"
import { PostCard } from "@/components/post-card"
import { PaperCard } from "@/components/paper-card"
import { AskAIModal } from "@/components/ask-ai-modal"
import { useAuthStore } from "@/lib/store"
import { searchPapers, searchPosts, votePost, removeVotePost, votePaper, removeVotePaper } from "@/lib/api"
import { QUICK_FILTER_TOPICS } from "@/lib/types"
import type { PaperCard as PaperCardType, DiscussionPost, VoteType } from "@/lib/types"
import { cn } from "@/lib/utils"

function SearchContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const { user } = useAuthStore()
  
  const initialQuery = searchParams.get("q") || ""
  const [query, setQuery] = useState(initialQuery)
  const [activeTab, setActiveTab] = useState<"papers" | "discussions">("papers")
  const [selectedFilter, setSelectedFilter] = useState<string | null>(null)
  const [askAIPaper, setAskAIPaper] = useState<PaperCardType | null>(null)
  const [userVotes, setUserVotes] = useState<Record<string, VoteType>>({})

  // Update query when URL changes
  useEffect(() => {
    const q = searchParams.get("q")
    if (q) setQuery(q)
  }, [searchParams])

  // Search papers
  const { data: papersData, error: papersError, isLoading: papersLoading, mutate: mutatePapers } = useSWR(
    initialQuery ? `search-papers-${initialQuery}-${selectedFilter}` : null,
    () => searchPapers(initialQuery, selectedFilter ? [selectedFilter] : undefined),
    { revalidateOnFocus: false }
  )

  // Search posts
  const { data: postsData, error: postsError, isLoading: postsLoading, mutate: mutatePosts } = useSWR(
    initialQuery ? `search-posts-${initialQuery}-${selectedFilter}` : null,
    () => searchPosts(initialQuery, selectedFilter ? [selectedFilter] : undefined),
    { revalidateOnFocus: false }
  )

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      router.push(`/search?q=${encodeURIComponent(query.trim())}`)
    }
  }

  const handleFilterClick = (topic: string) => {
    if (selectedFilter === topic) {
      setSelectedFilter(null)
    } else {
      setSelectedFilter(topic)
    }
  }

  const handleVotePost = useCallback(
    async (postId: string, vote: "upvote" | "downvote") => {
      if (!user) {
        toast.error("Please log in to vote")
        return
      }
      const prevVote = userVotes[postId]
      setUserVotes((prev) => ({ ...prev, [postId]: vote }))
      try {
        await votePost(postId, vote)
      } catch {
        setUserVotes((prev) => ({ ...prev, [postId]: prevVote }))
        toast.error("Failed to vote")
      }
    },
    [user, userVotes]
  )

  const handleRemoveVotePost = useCallback(
    async (postId: string) => {
      const prevVote = userVotes[postId]
      setUserVotes((prev) => ({ ...prev, [postId]: null }))
      try {
        await removeVotePost(postId, prevVote!)
      } catch {
        setUserVotes((prev) => ({ ...prev, [postId]: prevVote }))
        toast.error("Failed to remove vote")
      }
    },
    [userVotes]
  )

  const handleVotePaper = useCallback(
    async (paperId: string, vote: "upvote" | "downvote") => {
      if (!user) {
        toast.error("Please log in to vote")
        return
      }
      const prevVote = userVotes[paperId]
      setUserVotes((prev) => ({ ...prev, [paperId]: vote }))
      try {
        await votePaper(paperId, vote)
      } catch {
        setUserVotes((prev) => ({ ...prev, [paperId]: prevVote }))
        toast.error("Failed to vote")
      }
    },
    [user, userVotes]
  )

  const handleRemoveVotePaper = useCallback(
    async (paperId: string) => {
      const prevVote = userVotes[paperId]
      setUserVotes((prev) => ({ ...prev, [paperId]: null }))
      try {
        await removeVotePaper(paperId, prevVote!)
      } catch {
        setUserVotes((prev) => ({ ...prev, [paperId]: prevVote }))
        toast.error("Failed to remove vote")
      }
    },
    [userVotes]
  )

  const papers = papersData?.items ?? []
  const posts = postsData?.items ?? []

  return (
    <div className="max-w-4xl mx-auto">
      {/* Search header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-4">Search</h1>
        
        {/* Search form */}
        <form onSubmit={handleSearch} className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search papers and discussions..."
            className="pl-9 pr-24"
          />
          <Button
            type="submit"
            size="sm"
            className="absolute right-1.5 top-1/2 -translate-y-1/2"
          >
            Search
          </Button>
        </form>

        {/* Quick filters */}
        <div className="flex flex-wrap gap-2 mt-4">
          {QUICK_FILTER_TOPICS.map((topic) => (
            <Badge
              key={topic}
              variant={selectedFilter === topic ? "default" : "secondary"}
              className={cn(
                "cursor-pointer transition-colors",
                selectedFilter === topic
                  ? ""
                  : "hover:bg-primary hover:text-primary-foreground"
              )}
              onClick={() => handleFilterClick(topic)}
            >
              {topic}
            </Badge>
          ))}
        </div>
      </div>

      {/* Results */}
      {initialQuery ? (
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "papers" | "discussions")}>
          <TabsList className="mb-4">
            <TabsTrigger value="papers">
              Papers {papers.length > 0 && `(${papers.length})`}
            </TabsTrigger>
            <TabsTrigger value="discussions">
              Discussions {posts.length > 0 && `(${posts.length})`}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="papers">
            {papersLoading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="rounded-lg border p-5 space-y-3">
                    <Skeleton className="h-4 w-32" />
                    <Skeleton className="h-6 w-full" />
                    <Skeleton className="h-20 w-full" />
                  </div>
                ))}
              </div>
            ) : papersError ? (
              <div className="text-center py-12">
                <p className="text-muted-foreground mb-4">Failed to search papers</p>
                <Button variant="outline" onClick={() => mutatePapers()}>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Try again
                </Button>
              </div>
            ) : papers.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-muted-foreground">
                  No papers found for &quot;{initialQuery}&quot;
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {papers.map((paper) => (
                  <PaperCard
                    key={paper.id}
                    paper={paper}
                    userVote={userVotes[paper.id]}
                    onVote={(vote) => handleVotePaper(paper.id, vote)}
                    onRemoveVote={() => handleRemoveVotePaper(paper.id)}
                    onAskAI={() => setAskAIPaper(paper)}
                  />
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="discussions">
            {postsLoading ? (
              <div className="space-y-4">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="rounded-lg border p-4">
                    <div className="flex gap-3">
                      <Skeleton className="h-20 w-12" />
                      <div className="flex-1 space-y-2">
                        <Skeleton className="h-4 w-32" />
                        <Skeleton className="h-6 w-full" />
                        <Skeleton className="h-4 w-24" />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : postsError ? (
              <div className="text-center py-12">
                <p className="text-muted-foreground mb-4">Failed to search discussions</p>
                <Button variant="outline" onClick={() => mutatePosts()}>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Try again
                </Button>
              </div>
            ) : posts.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-muted-foreground">
                  No discussions found for &quot;{initialQuery}&quot;
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {posts.map((post) => (
                  <PostCard
                    key={post.id}
                    post={post}
                    userVote={userVotes[post.id]}
                    onVote={(vote) => handleVotePost(post.id, vote)}
                    onRemoveVote={() => handleRemoveVotePost(post.id)}
                    onAskAI={
                      post.linked_paper
                        ? () => setAskAIPaper(post.linked_paper!)
                        : undefined
                    }
                  />
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      ) : (
        <div className="text-center py-12">
          <Search className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
          <p className="text-muted-foreground">
            Enter a search term to find papers and discussions
          </p>
        </div>
      )}

      {/* Ask AI Modal */}
      {askAIPaper && (
        <AskAIModal
          paper={askAIPaper}
          open={!!askAIPaper}
          onOpenChange={(open) => !open && setAskAIPaper(null)}
        />
      )}
    </div>
  )
}

export default function SearchPage() {
  return (
    <Suspense fallback={
      <div className="max-w-4xl mx-auto">
        <Skeleton className="h-8 w-32 mb-4" />
        <Skeleton className="h-10 w-full mb-4" />
        <div className="flex gap-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-6 w-16 rounded-full" />
          ))}
        </div>
      </div>
    }>
      <SearchContent />
    </Suspense>
  )
}
