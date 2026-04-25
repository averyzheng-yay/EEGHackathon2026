"use client"

import { useState, useEffect, useRef } from "react"
import { useRouter } from "next/navigation"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { toast } from "sonner"
import { X, Plus, BookOpen, Search, Loader2 } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { FieldGroup, Field, FieldLabel } from "@/components/ui/field"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Spinner } from "@/components/ui/spinner"
import { createPost, searchPapers } from "@/lib/api"
import type { TechnicalLevel, PaperCard } from "@/lib/types"

const postSchema = z.object({
  title: z
    .string()
    .min(10, "Title must be at least 10 characters")
    .max(200, "Title must be 200 characters or less"),
  content: z
    .string()
    .min(20, "Content must be at least 20 characters")
    .max(10000, "Content must be 10,000 characters or less"),
  technical_level: z.enum(["beginner", "intermediate", "expert"]),
})

type PostForm = z.infer<typeof postSchema>

interface CreatePostModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function CreatePostModal({ open, onOpenChange }: CreatePostModalProps) {
  const router = useRouter()
  const [tags, setTags] = useState<string[]>([])
  const [tagInput, setTagInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  // Paper picker state
  const [paperQuery, setPaperQuery] = useState("")
  const [paperResults, setPaperResults] = useState<PaperCard[]>([])
  const [selectedPaper, setSelectedPaper] = useState<PaperCard | null>(null)
  const [searchingPapers, setSearchingPapers] = useState(false)
  const [showDropdown, setShowDropdown] = useState(false)
  const searchRef = useRef<HTMLDivElement>(null)

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { errors },
  } = useForm<PostForm>({
    resolver: zodResolver(postSchema),
    defaultValues: { technical_level: "intermediate" },
  })

  const technicalLevel = watch("technical_level")

  // Debounced paper search
  useEffect(() => {
    if (!paperQuery.trim() || selectedPaper) {
      setPaperResults([])
      setShowDropdown(false)
      return
    }
    const timer = setTimeout(async () => {
      setSearchingPapers(true)
      try {
        const results = await searchPapers(paperQuery)
        setPaperResults(results.items.slice(0, 6))
        setShowDropdown(results.items.length > 0)
      } catch {
        setPaperResults([])
      } finally {
        setSearchingPapers(false)
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [paperQuery, selectedPaper])

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener("mousedown", handler)
    return () => document.removeEventListener("mousedown", handler)
  }, [])

  const addTag = () => {
    const tag = tagInput.trim().toLowerCase()
    if (tag && !tags.includes(tag) && tags.length < 8) {
      setTags([...tags, tag])
      setTagInput("")
    }
  }

  const removeTag = (t: string) => setTags(tags.filter((x) => x !== t))

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") { e.preventDefault(); addTag() }
  }

  const onSubmit = async (data: PostForm) => {
    setIsLoading(true)
    try {
      const post = await createPost({
        ...data,
        tags,
        linked_paper_id: selectedPaper?.id,
      })
      toast.success("Post created!")
      reset()
      setTags([])
      setSelectedPaper(null)
      setPaperQuery("")
      onOpenChange(false)
      router.push(`/posts/${post.id}`)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to create post")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create a discussion</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)}>
          <FieldGroup>
            <Field>
              <FieldLabel htmlFor="title">Title</FieldLabel>
              <Input
                id="title"
                placeholder="What do you want to discuss?"
                {...register("title")}
              />
              {errors.title && (
                <p className="text-sm text-destructive">{errors.title.message}</p>
              )}
            </Field>

            <Field>
              <FieldLabel htmlFor="content">Content</FieldLabel>
              <Textarea
                id="content"
                placeholder="Share your thoughts, questions, or findings..."
                rows={6}
                {...register("content")}
              />
              {errors.content && (
                <p className="text-sm text-destructive">{errors.content.message}</p>
              )}
            </Field>

            {/* Paper reference picker */}
            <Field>
              <FieldLabel>Reference a Paper (optional)</FieldLabel>
              {selectedPaper ? (
                <div className="flex items-start gap-3 rounded-lg border p-3 bg-muted/40">
                  <BookOpen className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium line-clamp-2">{selectedPaper.title}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {selectedPaper.authors.slice(0, 3).join(", ")}
                      {selectedPaper.authors.length > 3 && ` +${selectedPaper.authors.length - 3} more`}
                      {selectedPaper.year && ` · ${selectedPaper.year}`}
                    </p>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 shrink-0"
                    onClick={() => { setSelectedPaper(null); setPaperQuery("") }}
                  >
                    <X className="h-3.5 w-3.5" />
                  </Button>
                </div>
              ) : (
                <div ref={searchRef} className="relative">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search papers by title or keyword..."
                      value={paperQuery}
                      onChange={(e) => setPaperQuery(e.target.value)}
                      onFocus={() => paperResults.length > 0 && setShowDropdown(true)}
                      className="pl-9"
                    />
                    {searchingPapers && (
                      <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-muted-foreground" />
                    )}
                  </div>
                  {showDropdown && paperResults.length > 0 && (
                    <div className="absolute z-50 w-full mt-1 rounded-lg border bg-popover shadow-md overflow-hidden">
                      {paperResults.map((paper) => (
                        <button
                          key={paper.id}
                          type="button"
                          className="w-full text-left px-3 py-2.5 hover:bg-accent transition-colors border-b last:border-b-0"
                          onMouseDown={(e) => {
                            e.preventDefault()
                            setSelectedPaper(paper)
                            setPaperQuery("")
                            setShowDropdown(false)
                          }}
                        >
                          <p className="text-sm font-medium line-clamp-1">{paper.title}</p>
                          <p className="text-xs text-muted-foreground mt-0.5">
                            {paper.authors.slice(0, 2).join(", ")}
                            {paper.authors.length > 2 && " et al."}
                            {paper.year && ` · ${paper.year}`}
                          </p>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </Field>

            <Field>
              <FieldLabel htmlFor="tags">Tags</FieldLabel>
              <div className="flex gap-2">
                <Input
                  id="tags"
                  placeholder="Add a tag and press Enter"
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  disabled={tags.length >= 8}
                />
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  onClick={addTag}
                  disabled={tags.length >= 8}
                >
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
              {tags.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {tags.map((tag) => (
                    <Badge key={tag} variant="secondary" className="gap-1">
                      {tag}
                      <button type="button" onClick={() => removeTag(tag)} className="ml-1 hover:text-destructive">
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
              )}
              <p className="text-xs text-muted-foreground">{tags.length}/8 tags</p>
            </Field>

            <Field>
              <FieldLabel>Technical Level</FieldLabel>
              <Select
                value={technicalLevel}
                onValueChange={(value: TechnicalLevel) => setValue("technical_level", value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="beginner">Beginner — Accessible to everyone</SelectItem>
                  <SelectItem value="intermediate">Intermediate — Some background helpful</SelectItem>
                  <SelectItem value="expert">Expert — Technical discussion</SelectItem>
                </SelectContent>
              </Select>
            </Field>

            <div className="flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={isLoading}>
                {isLoading ? <Spinner className="mr-2" /> : null}
                Post
              </Button>
            </div>
          </FieldGroup>
        </form>
      </DialogContent>
    </Dialog>
  )
}
