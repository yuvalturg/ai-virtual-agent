export interface KnowledgeBase {
  id?: string;
  name: string;
  version: string;
  embedding_model: string;
  provider_id?: string;
  vector_db_name: string;
  is_external: boolean;
  source?: string;
  source_configuration?: string;
  created_by?: string;
}

export interface Tool {
  id: string;
  name: string;
  title: string;
}

export interface Model {
  id: string;
  name: string;
  model_type: string;
}
