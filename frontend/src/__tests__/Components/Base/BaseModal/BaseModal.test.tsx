// Third Party
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import BaseModal from "@/Components/Base/BaseModal";
import type { ModalData } from "@/Components/Base/BaseModal";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

const confirmData: ModalData = {
  modal_id: "delete",
  title: "Delete Item",
  text: "Delete?",
  icon: "fas fa-trash",
  url: "/delete/1/",
  color: "danger",
  buttonText: "Delete",
};

describe("BaseModal", () => {
  describe("default variant", () => {
    it("should render title, children and default close button when shown", () => {
      // Test Data
      render(
        <BaseModal title="Details" show onHide={vi.fn()}>
          <p>Body content</p>
        </BaseModal>,
      );

      // Test Action
      const dialog = screen.getByRole("dialog");

      // Expected Result
      expect(dialog).toBeInTheDocument();
      expect(screen.getByText("Details")).toBeInTheDocument();
      expect(screen.getByText("Body content")).toBeInTheDocument();
      // Header "X" + Footer button
      expect(screen.getAllByRole("button", { name: "Close" })).toHaveLength(2);
    });

    it("should call onHide when close button is clicked", async () => {
      // Test Data
      const onHide = vi.fn();
      const user = userEvent.setup();
      render(
        <BaseModal title="Details" show onHide={onHide} closeText="Dismiss">
          <p>Body</p>
        </BaseModal>,
      );

      // Test Action
      await user.click(screen.getByRole("button", { name: "Dismiss" }));

      // Expected Result
      expect(onHide).toHaveBeenCalledTimes(1);
    });

    it("should render custom footer or hide footer when configured", () => {
      // Test Data
      const { rerender } = render(
        <BaseModal title="Details" show onHide={vi.fn()} footer={<span>Custom footer</span>}>
          <p>Body</p>
        </BaseModal>,
      );

      // Test Action
      const customFooter = screen.getByText("Custom footer");
      rerender(
        <BaseModal title="Details" show onHide={vi.fn()} hideFooter closeButton={false}>
          <p>Body</p>
        </BaseModal>,
      );

      // Expected Result
      expect(customFooter).toBeTruthy();
      expect(screen.queryByText("Custom footer")).not.toBeInTheDocument();
      expect(screen.queryByRole("button")).not.toBeInTheDocument();
    });
  });

  describe("confirm variant", () => {
    it("should call onApprove with url and close modal on success", async () => {
      // Test Data
      const onApprove = vi.fn().mockResolvedValue(undefined);
      const setShowModal = vi.fn();
      const user = userEvent.setup();
      render(
        <BaseModal
          variant="confirm"
          data={confirmData}
          showModal
          setShowModal={setShowModal}
          onApprove={onApprove}
        >
          <p>Really delete?</p>
        </BaseModal>,
      );

      // Test Action
      await user.click(screen.getByRole("button", { name: "Delete" }));

      // Expected Result
      expect(screen.getByText("Delete Item")).toBeInTheDocument();
      expect(screen.getByText("Really delete?")).toBeInTheDocument();
      expect(onApprove).toHaveBeenCalledWith({ url: "/delete/1/", formData: {} });
      await waitFor(() => expect(setShowModal).toHaveBeenCalledWith(false));
    });

    it("should show error alert when onApprove rejects", async () => {
      // Test Data
      const onApprove = vi.fn().mockRejectedValue(new Error("Failed"));
      const user = userEvent.setup();
      render(
        <BaseModal
          variant="confirm"
          data={confirmData}
          showModal
          setShowModal={vi.fn()}
          onApprove={onApprove}
        />,
      );

      // Test Action
      await user.click(screen.getByRole("button", { name: "Delete" }));

      // Expected Result
      expect(await screen.findByText("Failed")).toBeInTheDocument();
    });

    it("should pass form data from render children and block approve when invalid", async () => {
      // Test Data
      const onApprove = vi.fn().mockResolvedValue(undefined);
      const user = userEvent.setup();
      render(
        <BaseModal
          variant="confirm"
          data={confirmData}
          confirmText="Save"
          showModal
          setShowModal={vi.fn()}
          onApprove={onApprove}
          initialFormData={{ name: "" }}
          validate={(formData) => formData.name !== ""}
        >
          {({ formData, onChange }) => (
            <input
              aria-label="Name"
              value={String(formData.name ?? "")}
              onChange={(event) => onChange({ ...formData, name: event.target.value })}
            />
          )}
        </BaseModal>,
      );

      // Test Action
      await user.click(screen.getByRole("button", { name: "Save" }));
      const callsBeforeInput = onApprove.mock.calls.length;
      await user.type(screen.getByLabelText("Name"), "Veldspar");
      await user.click(screen.getByRole("button", { name: "Save" }));

      // Expected Result
      expect(callsBeforeInput).toBe(0);
      expect(onApprove).toHaveBeenCalledWith({ url: "/delete/1/", formData: { name: "Veldspar" } });
    });
  });
});
