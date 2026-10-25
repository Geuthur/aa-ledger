// Third Party
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { OwnerPortrait } from "@/Components/Base/OwnerPortrait";

describe("OwnerPortrait", () => {
  it("should render the image when a source is given", () => {
    // Test Data
    const src = "https://images.evetech.net/characters/1/portrait?size=64";

    // Test Action
    render(<OwnerPortrait src={src} alt="Pilot Alpha" />);

    // Expected Result
    expect(screen.getByRole("img", { name: "Pilot Alpha" })).toHaveAttribute("src", src);
  });

  it("should render the fallback icon when no source is given", () => {
    // Test Data
    const alt = "Acme Corp";

    // Test Action
    const { container } = render(<OwnerPortrait alt={alt} type="corporation" />);

    // Expected Result
    expect(screen.getByRole("img", { name: alt })).toBeInTheDocument();
    expect(container.querySelector("svg")).toBeInTheDocument();
    expect(container.querySelector("img")).not.toBeInTheDocument();
  });

  it("should hide the fallback from assistive tech when no alt text is given", () => {
    // Test Data
    // (no alt text)

    // Test Action
    const { container } = render(<OwnerPortrait />);

    // Expected Result
    expect(container.firstElementChild).toHaveAttribute("aria-hidden", "true");
  });

  it("should use the rounded shape and border when requested", () => {
    // Test Data
    const src = "https://example.test/corp.png";

    // Test Action
    render(<OwnerPortrait src={src} alt="Corp" shape="rounded" bordered />);

    // Expected Result
    const image = screen.getByRole("img", { name: "Corp" });
    expect(image).toHaveClass("rounded", "border");
    expect(image).not.toHaveClass("rounded-circle");
  });
});
