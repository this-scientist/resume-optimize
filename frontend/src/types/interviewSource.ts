/** API：InterviewSourceRead / InterviewSourceDetail */

export type InterviewSourceListItem = {
  id: number;
  kind: string;
  url: string | null;
  title: string | null;
  body_preview: string;
  fetch_status: string;
  index_status: string;
  created_at: string;
  embedding_model?: string | null;
};

export type InterviewSourceDetail = Omit<
  InterviewSourceListItem,
  "body_preview"
> & {
  body_md: string;
};
