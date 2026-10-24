// React
import React, { useMemo, useState } from "react";

// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ShieldAlert,
  Trash2,
} from "lucide-react";
import { parseAsInteger, parseAsString, useQueryState } from "nuqs";
import {
  Alert,
  Badge,
  Button,
  ButtonGroup,
  Card,
  Form,
  Modal,
  Spinner,
} from "react-bootstrap";
import { useTranslation } from "react-i18next";

// Styles
import styles from "@/Styles/modules/Administration.module.css";

// AA Ledger
import {
  deleteAdministrationOwner,
  loadAdministrationOwners,
  loadUserData,
  queueUpdate,
  triggerAdministrationOwnerUpdate,
} from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import type { AdministrationOwnerSchema } from "@/Api/schema";
import {
  AdministrationInspectionView,
  AdministrationKpiCards,
  AdministrationOwnersTable,
  AdministrationTaskPanel,
} from "@/Components/Administration";

export const AdministrationPage: React.FC = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  // URL State via nuqs for browser Back / Forward history
  const [inspectOwnerId, setInspectOwnerId] = useQueryState(
    "inspect",
    parseAsInteger
  );
  const [inspectOwnerType, setInspectOwnerType] = useQueryState(
    "type",
    parseAsString
  );

  // Local UI State
  const [searchTerm, setSearchTerm] = useState("");
  const [typeFilter, setTypeFilter] = useState<"all" | "character" | "corporation" | "alliance" | "issues">("all");
  const [showTaskPanel, setShowTaskPanel] = useState(false);
  const [forceRefreshGlobal, setForceRefreshGlobal] = useState(false);
  const [updatingKey, setUpdatingKey] = useState<string | null>(null);
  const [taskFeedback, setTaskFeedback] = useState<{
    variant: "success" | "danger";
    message: string;
  } | null>(null);

  // Delete Modal State
  const [ownerToDelete, setOwnerToDelete] = useState<AdministrationOwnerSchema | null>(null);

  // Queries
  const {
    data: owners,
    isLoading,
    isError,
  } = useQuery({
    queryKey: queryKeys.AdministrationOwners,
    queryFn: loadAdministrationOwners,
  });

  const { data: userData } = useQuery({
    queryKey: queryKeys.User,
    queryFn: loadUserData,
  });
  const isSuperuser = userData?.user.is_superuser ?? false;

  // Single Owner Update Mutation
  const singleUpdateMutation = useMutation({
    mutationFn: ({
      ownerType,
      ownerId,
      forceRefresh,
    }: {
      ownerType: "character" | "corporation";
      ownerId: number;
      forceRefresh: boolean;
    }) =>
      triggerAdministrationOwnerUpdate(ownerType, ownerId, {
        force_refresh: forceRefresh,
      }),
    onMutate: ({ ownerType, ownerId }) => {
      setUpdatingKey(`${ownerType}-${ownerId}`);
    },
    onSuccess: (data) => {
      setTaskFeedback({ variant: "success", message: data.message });
      queryClient.invalidateQueries({ queryKey: queryKeys.AdministrationOwners });
    },
    onError: (err: Error) => {
      setTaskFeedback({ variant: "danger", message: err.message });
    },
    onSettled: () => {
      setUpdatingKey(null);
    },
  });

  // Global Queue Update Mutation (All Characters or All Corporations)
  const globalQueueMutation = useMutation({
    mutationFn: ({
      target,
      forceRefresh,
    }: {
      target: "characters" | "corporations";
      forceRefresh: boolean;
    }) =>
      queueUpdate({
        target,
        eve_id: null,
        force_refresh: forceRefresh,
      }),
    onSuccess: (data) => {
      setTaskFeedback({ variant: "success", message: data.message });
      queryClient.invalidateQueries({ queryKey: queryKeys.AdministrationOwners });
    },
    onError: (err: Error) => {
      setTaskFeedback({ variant: "danger", message: err.message });
    },
  });

  // Delete Mutation
  const deleteMutation = useMutation({
    mutationFn: ({
      ownerType,
      ownerId,
    }: {
      ownerType: "character" | "corporation";
      ownerId: number;
    }) => deleteAdministrationOwner(ownerType, ownerId),
    onSuccess: (data) => {
      setTaskFeedback({ variant: "success", message: data.message });
      setOwnerToDelete(null);
      queryClient.invalidateQueries({ queryKey: queryKeys.AdministrationOwners });
    },
    onError: (err: Error) => {
      setTaskFeedback({ variant: "danger", message: err.message });
    },
  });

  // Metrics
  const metrics = useMemo(() => {
    if (!owners) return { total: 0, characters: 0, corporations: 0, alliances: 0, issues: 0 };
    return {
      total: owners.length,
      characters: owners.filter((o) => o.owner_type === "character").length,
      corporations: owners.filter((o) => o.owner_type === "corporation").length,
      alliances: owners.filter((o) => o.owner_type === "alliance").length,
      issues: owners.filter(
        (o) => o.status === "token_error" || Boolean(o.error_message)
      ).length,
    };
  }, [owners]);

  // Filtered Owners
  const filteredOwners = useMemo(() => {
    if (!owners) return [];
    return owners.filter((owner) => {
      if (typeFilter !== "all") {
        if (typeFilter === "issues") {
          const hasIssue =
            owner.status === "error" ||
            owner.status === "token_error" ||
            Boolean(owner.error_message);
          if (!hasIssue) return false;
        } else if (owner.owner_type !== typeFilter) {
          return false;
        }
      }
      if (searchTerm.trim()) {
        const query = searchTerm.toLowerCase();
        const matchesName = owner.name.toLowerCase().includes(query);
        const matchesTicker = owner.ticker?.toLowerCase().includes(query);
        const matchesUser = owner.user_name?.toLowerCase().includes(query);
        const matchesAlts = owner.alts?.some((alt) =>
          alt.character_name.toLowerCase().includes(query)
        );
        return Boolean(matchesName || matchesTicker || matchesUser || matchesAlts);
      }
      return true;
    });
  }, [owners, typeFilter, searchTerm]);

  // If inspection subview is active in URL query params
  if (inspectOwnerId !== null && inspectOwnerType) {
    const validOwnerType =
      inspectOwnerType === "alliance"
        ? "alliance"
        : inspectOwnerType === "corporation"
        ? "corporation"
        : "character";
    return (
      <Card className="d-flex flex-column gap-3">
        <Card.Body>
          <header className="d-flex align-items-center gap-3 mb-4">
            <div className="p-2 rounded bg-danger-subtle text-danger border border-danger-subtle">
              <ShieldAlert size={28} />
            </div>
            <div>
              <h1 className="h3 mb-1 fw-bold">{t("Administration")}</h1>
              <p className="mb-0 small text-muted">
                {t("System-wide transaction ledger management, synchronization tasks, and owner audits.")}
              </p>
            </div>
          </header>
          <AdministrationInspectionView
            ownerType={validOwnerType}
            ownerId={inspectOwnerId}
            onBack={() => {
              setInspectOwnerId(null);
              setInspectOwnerType(null);
            }}
          />
        </Card.Body>
      </Card>
    );
  }

  return (
    <Card className="bg-dark d-flex flex-column gap-3">
      <Card.Body>
        <header className="d-flex align-items-center gap-3 mb-4">
          <div className="p-2 rounded bg-danger-subtle text-danger border border-danger-subtle">
            <ShieldAlert size={28} />
          </div>
          <div>
            <h1 className="h3 mb-1 fw-bold">{t("Administration")}</h1>
            <p className="mb-0 small text-muted">
              {t("System-wide transaction ledger management, synchronization tasks, and owner audits.")}
            </p>
          </div>
        </header>

        {/* Feedback alert */}
        {taskFeedback && (
          <Alert
            variant={taskFeedback.variant}
            dismissible
            onClose={() => setTaskFeedback(null)}
          >
            <span data-testid="task-feedback-message">{taskFeedback.message}</span>
          </Alert>
        )}

        {/* Global Statistics Cards */}
        <AdministrationKpiCards metrics={metrics} />

        {/* Global Task Update Panel (Collapsible) - Only for Superusers */}
        {isSuperuser && (
          <AdministrationTaskPanel
            showTaskPanel={showTaskPanel}
            onToggleTaskPanel={() => setShowTaskPanel((prev) => !prev)}
            forceRefreshGlobal={forceRefreshGlobal}
            onToggleForceRefresh={setForceRefreshGlobal}
            isPending={globalQueueMutation.isPending}
            onUpdateTarget={(target) =>
              globalQueueMutation.mutate({
                target,
                forceRefresh: forceRefreshGlobal,
              })
            }
          />
        )}

        {/* Filters and Search Bar */}
        <div className="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-2 mt-4 mb-2">
          <ButtonGroup size="sm">
            <Button
              variant={typeFilter === "all" ? "primary" : "secondary"}
              onClick={() => setTypeFilter("all")}
            >
              {t("All")} <Badge bg="secondary" className="ms-1">{metrics.total}</Badge>
            </Button>
            <Button
              variant={typeFilter === "character" ? "primary" : "secondary"}
              onClick={() => setTypeFilter("character")}
            >
              {t("Characters")} <Badge bg="secondary" className="ms-1">{metrics.characters}</Badge>
            </Button>
            <Button
              variant={typeFilter === "corporation" ? "primary" : "secondary"}
              onClick={() => setTypeFilter("corporation")}
            >
              {t("Corporations")} <Badge bg="secondary" className="ms-1">{metrics.corporations}</Badge>
            </Button>
            <Button
              variant={typeFilter === "alliance" ? "primary" : "secondary"}
              onClick={() => setTypeFilter("alliance")}
            >
              {t("Alliances")} <Badge bg="secondary" className="ms-1">{metrics.alliances}</Badge>
            </Button>
            <Button
              variant={typeFilter === "issues" ? "primary" : "secondary"}
              onClick={() => setTypeFilter("issues")}
            >
              {t("Issues")} <Badge bg="secondary" className="ms-1">{metrics.issues}</Badge>
            </Button>
          </ButtonGroup>

          <div className={styles.searchContainer}>
            <Form.Control
              type="search"
              placeholder={t("Search owners…")}
              size="sm"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-dark text-light border-secondary"
              aria-label={t("Search owners")}
            />
          </div>
        </div>

        {/* Owners Table */}
        <AdministrationOwnersTable
          owners={filteredOwners}
          isLoading={isLoading}
          isError={isError}
          updatingKey={updatingKey}
          isSuperuser={isSuperuser}
          onInspect={(owner) => {
            setInspectOwnerType(owner.owner_type);
            setInspectOwnerId(owner.owner_id);
          }}
          onTriggerUpdate={(ownerType, ownerId, forceRefresh) => {
            singleUpdateMutation.mutate({ ownerType, ownerId, forceRefresh });
          }}
          onDelete={(owner) => setOwnerToDelete(owner)}
        />

        {/* Delete Confirmation Modal */}
        <Modal
          show={ownerToDelete !== null}
          onHide={() => setOwnerToDelete(null)}
          centered
        >
          <Modal.Header closeButton>
            <Modal.Title className="d-flex align-items-center gap-2 text-danger">
              <ShieldAlert size={20} />
              {t("Confirm Deletion")}
            </Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <p>
              {t("Are you sure you want to delete")} <strong>{ownerToDelete?.name}</strong>?
            </p>
            <Alert variant="warning" className="small">
              {t(
                "This action will remove the owner and all associated journal, mining, and planetary records from the ledger. This cannot be undone."
              )}
            </Alert>
          </Modal.Body>
          <Modal.Footer>
            <Button
              variant="secondary"
              onClick={() => setOwnerToDelete(null)}
              disabled={deleteMutation.isPending}
            >
              {t("Cancel")}
            </Button>
            <Button
              variant="danger"
              disabled={deleteMutation.isPending}
              onClick={() => {
                if (ownerToDelete && ownerToDelete.owner_type !== "alliance") {
                  deleteMutation.mutate({
                    ownerType: ownerToDelete.owner_type,
                    ownerId: ownerToDelete.owner_id,
                  });
                }
              }}
              data-testid="confirm-delete-btn"
            >
              {deleteMutation.isPending ? (
                <Spinner size="sm" animation="border" className="me-1" />
              ) : (
                <Trash2 size={14} className="me-1" />
              )}
              {t("Delete Owner")}
            </Button>
          </Modal.Footer>
        </Modal>
      </Card.Body>
    </Card>
  );
};

export default AdministrationPage;
