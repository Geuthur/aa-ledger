// React
import type React from "react";

export interface BaseOwnerSection {
  section: string;
  section_name: string;
  is_success?: boolean | null;
  has_token_error?: boolean | null;
  error_message?: string | null;
  last_run_at?: string | null;
  last_run_finished_at?: string | null;
}

export interface BaseOwner {
  id: number;
  name: string;
  owner_type?: "character" | "corporation" | "alliance" | string;
  avatar_url?: string | null;
  subtitle?: string | null;
  status: string; // "ok", "error", "token_error", "disabled", "incomplete"
  has_error?: boolean;
  error_message?: string | null;
  last_sync?: string | null;
  sections?: BaseOwnerSection[] | null;
}

export interface BaseMissingOwner {
  id: number;
  name: string;
  /** Defaults to "character" when filtering. */
  owner_type?: "character" | "corporation" | "alliance" | string;
  avatar_url?: string | null;
  subtitle?: string | null;
}

export interface BaseOwnerCardProps<T extends BaseOwner = BaseOwner> {
  owner: T;
  isUpdating?: boolean;
  cooldown?: number;
  onTriggerUpdate?: (ownerId: number) => void;
  onDeleteClick?: (owner: T) => void;
  /** Slot for project specific content (switches, statistics, ...). */
  renderCustomContent?: (owner: T) => React.ReactNode;
  /** Slot for additional action buttons on the left side of the footer. */
  renderActions?: (owner: T) => React.ReactNode;
}

export interface MissingOwnerCardProps<M extends BaseMissingOwner = BaseMissingOwner> {
  missing: M;
  appName?: string;
  actionUrl?: string;
  actionLabel?: string;
}

export interface BaseOwnerSettingsSectionProps<
  T extends BaseOwner = BaseOwner,
  M extends BaseMissingOwner = BaseMissingOwner,
> {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  owners?: T[];
  missingOwners?: M[];
  isLoading?: boolean;
  isError?: boolean;
  errorMessage?: string;
  emptyMessage?: string;
  appName?: string;

  /** Show type filter and search field (default: true). */
  enableFilters?: boolean;
  searchPlaceholder?: string;

  onUpdateAll?: () => void;
  isUpdatingAll?: boolean;
  globalCooldown?: number;

  feedbackMessage?: { variant: "success" | "danger"; text: string } | null;
  onDismissFeedback?: () => void;

  onTriggerSingleUpdate?: (ownerId: number) => void;
  /** Hide the update button for owners where this returns false (default: all updatable). */
  isUpdatable?: (owner: T) => boolean;
  /** Hide the delete button for owners where this returns false (default: all deletable). */
  isDeletable?: (owner: T) => boolean;
  updatingOwnerId?: number | null;
  ownerCooldowns?: Record<number, number>;
  onDeleteOwner?: (owner: T) => void | Promise<unknown>;
  isDeleting?: boolean;
  deleteModalTitle?: string;
  deleteModalDescription?: (owner: T) => React.ReactNode;

  renderCustomCardContent?: (owner: T) => React.ReactNode;
  renderCardActions?: (owner: T) => React.ReactNode;

  missingSectionTitle?: string;
  missingActionUrl?: string;
  missingActionLabel?: string;
}
