import { PageSection, Title } from '@patternfly/react-core';
import { createFileRoute } from '@tanstack/react-router';
import { KnowledgeBaseCard } from '@/components/knowledge-base-card';
import { KnowledgeBaseForm } from '@/components/knowledge-base-form';
import axios from '../../../../admin/src/api/axios.ts';
import { useState, useEffect } from 'react';

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

export const Route = createFileRoute('/config/knowledge-bases')({
  component: KnowledgeBases,
});

export function KnowledgeBases() {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);

  useEffect(() => {
    void fetchKbs();
  }, []);

  const fetchKbs = async () => {
    const res = await axios.get('/knowledge_bases');
    const kbs = res.data;

    if (kbs) {
      setKnowledgeBases(kbs);
    } else {
      setKnowledgeBases([
        {
          id: '1',
          name: 'apple',
          version: 'v1',
          embedding_model: 'llamastack',
          provider_id: '1',
          vector_db_name: 'pg_data',
          is_external: true,
          source: 'www',
          source_configuration: 'config',
          created_by: '2020-01-01',
        },
        {
          id: '2',
          name: 'orange',
          version: 'v1',
          embedding_model: 'llamastack',
          provider_id: '1',
          vector_db_name: 'pg_data',
          is_external: true,
          source: 'www',
          source_configuration: 'config',
          created_by: '2020-01-01',
        },
        {
          id: '3',
          name: 'grape',
          version: 'v1',
          embedding_model: 'llamastack',
          provider_id: '1',
          vector_db_name: 'pg_data',
          is_external: true,
          source: 'www',
          source_configuration: 'config',
          created_by: '2020-01-01',
        },
      ]);
    }
  };

  return (
    <PageSection hasBodyWrapper={false}>
      <Title headingLevel="h1">Knowledge Bases</Title>

      <PageSection className="pf-v5-u-mb-lg">
        <KnowledgeBaseForm />
        {knowledgeBases.map((knowledgebase) => (
          <KnowledgeBaseCard key={knowledgebase.id} knowledgeBase={knowledgebase} />
        ))}
      </PageSection>
    </PageSection>
  );
}
