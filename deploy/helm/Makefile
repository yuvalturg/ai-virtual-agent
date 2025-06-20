# Makefile for RAG Deployment
# Replaces the original deploy.sh script with additional uninstall functionality
ifeq ($(NAMESPACE),)
ifeq (,$(filter depend list-models% help,$(MAKECMDGOALS)))
$(error NAMESPACE is not set)
endif
endif

MAKEFLAGS += --no-print-directory

# Default values
POSTGRES_USER ?= postgres
POSTGRES_PASSWORD ?= rag_password
POSTGRES_DBNAME ?= rag_blueprint
MINIO_USER ?= minio_rag_user
MINIO_PASSWORD ?= minio_rag_password
HF_TOKEN ?= $(shell bash -c 'read -r -p "Enter Hugging Face Token: " HF_TOKEN; echo $$HF_TOKEN')
AI_VIRTUAL_ASSISTANT_CHART := ai-virtual-assistant
VECTORDB_INGESTION_MONIFTOR_CHART := vectordb-ingestion-monitor
TOLERATIONS_TEMPLATE=[{"key":"$(1)","effect":"NoSchedule","operator":"Exists"}]

#ingestion pipeline configuration
SOURCE ?= S3
EMBEDDING_MODEL ?= all-MiniLM-L6-v2
INGESTION_PIPELINE_NAME ?= demo-rag-vector-db
INGESTION_PIPELINE_VERSION ?= 1.0
ACCESS_KEY_ID ?= $(MINIO_USER)
SECRET_ACCESS_KEY ?= $(MINIO_PASSWORD)
BUCKET_NAME ?= documents
ENDPOINT_URL ?= http://minio:9000
REGION ?= us-east-1
# PDF file path variable for upload-pdf target
PDF_DIR = ../../notebooks
S3_TEMPLATE={"access_key_id":"$(1)","secret_access_key":"$(2)","bucket_name":"$(3)","endpoint_url":"$(4)","region":"$(5)"}

helm_pgvector_args = \
    --set pgvector.secret.user=$(POSTGRES_USER) \
    --set pgvector.secret.password=$(POSTGRES_PASSWORD) \
    --set pgvector.secret.dbname=$(POSTGRES_DBNAME)

helm_minio_args = \
    --set minio.secret.user=$(MINIO_USER) \
    --set minio.secret.password=$(MINIO_PASSWORD)

helm_llm_service_args = \
    --set llm-service.secret.hf_token=$(HF_TOKEN) \
    $(if $(LLM),--set global.models.$(LLM).enabled=true,) \
    $(if $(SAFETY),--set global.models.$(SAFETY).enabled=true,) \
    $(if $(LLM_TOLERATION),--set-json global.models.$(LLM).tolerations='$(call TOLERATIONS_TEMPLATE,$(LLM_TOLERATION))',) \
    $(if $(SAFETY_TOLERATION),--set-json global.models.$(SAFETY).tolerations='$(call TOLERATIONS_TEMPLATE,$(SAFETY_TOLERATION))',)

helm_llama_stack_args = \
    $(if $(LLM),--set global.models.$(LLM).enabled=true,) \
    $(if $(SAFETY),--set global.models.$(SAFETY).enabled=true,) \
    $(if $(LLM_URL),--set global.models.$(LLM).url='$(LLM_URL)',) \
    $(if $(SAFETY_URL),--set global.models.$(SAFETY).url='$(SAFETY_URL)',) \
    $(if $(LLM_API_TOKEN),--set global.models.$(LLM).apiToken='$(LLM_API_TOKEN)',) \
    $(if $(SAFETY_API_TOKEN),--set global.models.$(SAFETY).apiToken='$(SAFETY_API_TOKEN)',) \
    $(if $(LLAMA_STACK_ENV),--set-json llama-stack.secrets='$(LLAMA_STACK_ENV)',)

helm_ingestion_args = \
	$(if $(SOURCE),--set ingestion-pipeline.source='$(SOURCE)',) \
	$(if $(EMBEDDING_MODEL),--set ingestion-pipeline.embedding_model='$(EMBEDDING_MODEL)',) \
	$(if $(INGESTION_PIPELINE_NAME),--set ingestion-pipeline.name='$(INGESTION_PIPELINE_NAME)',) \
	$(if $(INGESTION_PIPELINE_VERSION),--set ingestion-pipeline.version='$(INGESTION_PIPELINE_VERSION)',) \
    $(if $(SOURCE),--set-json ingestion-pipeline.S3='$(call S3_TEMPLATE,$(ACCESS_KEY_ID),$(SECRET_ACCESS_KEY),$(BUCKET_NAME),$(ENDPOINT_URL),$(REGION))',)

# Default target
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  list-models   - List available models"
	@echo "  install       - Install the RAG deployment (creates namespace, secrets, and deploys Helm chart)"
	@echo "  uninstall     - Uninstall the RAG deployment and clean up resources"
	@echo "  status        - Check status of the deployment"
	@echo ""
	@echo "Configuration options (set via environment variables or make arguments):"
	@echo "  NAMESPACE                - Target namespace (default: llama-stack-rag)"
	@echo "  HF_TOKEN                 - Hugging Face Token (will prompt if not provided)"
	@echo "  {SAFETY,LLM}             - Model id as defined in values (eg. llama-3-2-1b-instruct)"
	@echo "  {SAFETY,LLM}_URL         - Model URL"
	@echo "  {SAFETY,LLM}_API_TOKEN   - Model API token for remote models"
	@echo "  {SAFETY,LLM}_TOLERATION  - Model pod toleration"

# Create namespace and deploy
namespace:
	@oc create namespace $(NAMESPACE) &> /dev/null && oc label namespace $(NAMESPACE) modelmesh-enabled=false ||:
	@oc project $(NAMESPACE) &> /dev/null ||:

.PHONY: depend
depend:
	@echo "Updating Helm dependencies"
	@helm dependency update $(AI_VIRTUAL_ASSISTANT_CHART) &> /dev/null

.PHONY: list-models
list-models: depend
	@helm template dummy-release $(AI_VIRTUAL_ASSISTANT_CHART) --set llm-service._debugListModels=true | grep ^model:

.PHONY: install
install: namespace depend
	@$(eval PGVECTOR_ARGS := $(call helm_pgvector_args))
	@$(eval MINIO_ARGS := $(call helm_minio_args))
	@$(eval LLM_SERVICE_ARGS := $(call helm_llm_service_args))
	@$(eval LLAMA_STACK_ARGS := $(call helm_llama_stack_args))
	@$(eval INGESTION_ARGS := $(call helm_ingestion_args))

	@echo "Installing $(AI_VIRTUAL_ASSISTANT_CHART) helm chart"
	@helm upgrade --install $(AI_VIRTUAL_ASSISTANT_CHART) $(AI_VIRTUAL_ASSISTANT_CHART) -n $(NAMESPACE) \
		$(PGVECTOR_ARGS) \
		$(MINIO_ARGS) \
		$(LLM_SERVICE_ARGS) \
		$(LLAMA_STACK_ARGS) \
		$(INGESTION_ARGS) \
		$(EXTRA_HELM_ARGS)
	@echo "Waiting for model services and llamastack to deploy. It may take around 10-15 minutes depending on the size of the model..."
	@oc rollout status deploy/llamastack -n $(NAMESPACE)
	@echo "$(AI_VIRTUAL_ASSISTANT_CHART) installed successfully"

	@echo "Installing $(VECTORDB_INGESTION_MONIFTOR_CHART) helm chart"
	@helm upgrade --install $(VECTORDB_INGESTION_MONIFTOR_CHART) $(VECTORDB_INGESTION_MONIFTOR_CHART) -n $(NAMESPACE)
	@echo "Waiting for ingestion pipeline monitor to deploy..."
	@oc rollout status deploy/ingestion-pipeline-monitor -n $(NAMESPACE)
	@echo "$(VECTORDB_INGESTION_MONIFTOR_CHART) installed successfully"

# Uninstall the deployment and clean up
.PHONY: uninstall
uninstall:
	@echo "Uninstalling $(AI_VIRTUAL_ASSISTANT_CHART) helm chart"
	@helm uninstall --ignore-not-found $(AI_VIRTUAL_ASSISTANT_CHART) -n $(NAMESPACE)
	@echo "Uninstalling $(VECTORDB_INGESTION_MONIFTOR_CHART) helm chart"
	@helm uninstall --ignore-not-found $(VECTORDB_INGESTION_MONIFTOR_CHART) -n $(NAMESPACE)
	@echo "Removing pgvector and minio PVCs from $(NAMESPACE)"
	@oc get pvc -n $(NAMESPACE) -o custom-columns=NAME:.metadata.name | grep -E '^(pg|minio)-data' | xargs -I {} oc delete pvc -n $(NAMESPACE) {} ||:
	@echo "Deleting remaining pods in namespace $(NAMESPACE)"
	@oc delete pods -n $(NAMESPACE) --all
	@echo "Checking for any remaining resources in namespace $(NAMESPACE)..."
	@echo "If you want to completely remove the namespace, run: oc delete project $(NAMESPACE)"
	@echo "Remaining resources in namespace $(NAMESPACE):"
	@$(MAKE) status

# Check deployment status
.PHONY: status
status:
	@echo "Listing pods..."
	oc get pods -n $(NAMESPACE) || true

	@echo "Listing services..."
	oc get svc -n $(NAMESPACE) || true

	@echo "Listing routes..."
	oc get routes -n $(NAMESPACE) || true

	@echo "Listing secrets..."
	oc get secrets -n $(NAMESPACE) | grep huggingface-secret || true

	@echo "Listing pvcs..."
	oc get pvc -n $(NAMESPACE) || true
