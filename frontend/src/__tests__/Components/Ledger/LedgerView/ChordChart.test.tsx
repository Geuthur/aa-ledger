// Third Party
import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import ChordChart from "@/Components/Ledger/LedgerView/ChordChart";

const billboard = {
  categories: [],
  series: [
    { from: "Alice", to: "Bounty", value: 100 },
    { from: "Bob", to: "ESS", value: 50 },
  ],
};

const mockReducedMotion = (reduced: boolean) => {
  vi.stubGlobal(
    "matchMedia",
    vi.fn().mockReturnValue({ matches: reduced, addEventListener: vi.fn(), removeEventListener: vi.fn() }),
  );
};

const ribbons = (container: HTMLElement) =>
  Array.from(container.querySelectorAll("svg > g:first-of-type > path"));

describe("ChordChart", () => {
  beforeEach(() => {
    mockReducedMotion(true);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  it("renders an arc and a label for every source and target", () => {
    // Test Action
    render(<ChordChart billboard={billboard} title="Distribution" />);

    // Expected Result
    expect(screen.getByRole("img", { name: "Distribution" })).toBeInTheDocument();
    for (const name of ["Alice", "Bob", "Bounty", "ESS"]) {
      expect(screen.getByText(name, { selector: "text" })).toBeInTheDocument();
    }
  });

  it("renders nothing without data", () => {
    // Test Action
    const { container } = render(<ChordChart billboard={null} />);

    // Expected Result
    expect(container).toBeEmptyDOMElement();
  });

  it("dims the flows that are not connected to the hovered node", () => {
    // Test Data
    const { container } = render(<ChordChart billboard={billboard} />);
    const [first, second] = ribbons(container);
    expect(first.getAttribute("fill-opacity")).toBe("0.7");

    // Test Action
    fireEvent.mouseEnter(screen.getByText("Alice", { selector: "text" }).parentElement as Element);

    // Expected Result
    expect(first.getAttribute("fill-opacity")).toBe("0.95");
    expect(Number(second.getAttribute("fill-opacity"))).toBeLessThan(0.1);
  });

  it("restores the flows when the pointer leaves the diagram", () => {
    // Test Data
    const { container } = render(<ChordChart billboard={billboard} />);
    const [first] = ribbons(container);
    fireEvent.mouseEnter(screen.getByText("Bob", { selector: "text" }).parentElement as Element);

    // Test Action
    fireEvent.mouseLeave(screen.getByRole("img"));

    // Expected Result
    expect(first.getAttribute("fill-opacity")).toBe("0.7");
  });

  it("fades the flows in while the diagram appears", () => {
    // Test Data
    mockReducedMotion(false);
    vi.useFakeTimers({ toFake: ["requestAnimationFrame", "cancelAnimationFrame", "performance"] });

    // Test Action
    const { container } = render(<ChordChart billboard={billboard} />);
    const [first] = ribbons(container);
    const initial = Number(first.getAttribute("fill-opacity"));
    act(() => {
      vi.advanceTimersByTime(1200);
    });

    // Expected Result
    expect(initial).toBe(0);
    expect(first.getAttribute("fill-opacity")).toBe("0.7");
  });

  it("sends a bullet along every flow", () => {
    // Test Data
    mockReducedMotion(false);

    // Test Action
    render(<ChordChart billboard={billboard} />);

    // Expected Result
    const bullets = screen.getAllByTestId("chord-bullet");
    expect(bullets).toHaveLength(2);
    for (const bullet of bullets) {
      const motion = bullet.querySelector("animateMotion");
      expect(motion?.getAttribute("repeatCount")).toBe("indefinite");
      expect(motion?.getAttribute("path")).toMatch(/^M.+Q0,0 /);
    }
  });

  it("does not animate bullets with reduced motion", () => {
    // Test Action
    render(<ChordChart billboard={billboard} />);

    // Expected Result
    expect(screen.queryAllByTestId("chord-bullet")).toHaveLength(0);
  });

  it("shows the flow and its amount in a tooltip", async () => {
    // Test Data
    const { container } = render(<ChordChart billboard={billboard} />);
    const [first] = ribbons(container);

    // Test Action
    fireEvent.mouseOver(first);

    // Expected Result
    expect(await screen.findByRole("tooltip")).toHaveTextContent("Alice → Bounty: 100 ISK");
  });

  it("removes a node and its flows when it is hidden in the legend", () => {
    // Test Data
    const { container } = render(<ChordChart billboard={billboard} />);
    expect(ribbons(container)).toHaveLength(2);

    // Test Action
    fireEvent.click(screen.getByRole("button", { name: "Hide Alice" }));

    // Expected Result
    expect(ribbons(container)).toHaveLength(1);
    expect(screen.queryByText("Alice", { selector: "text" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Show Alice" })).toHaveAttribute("aria-pressed", "false");
  });

  it("shows all nodes again", () => {
    // Test Data
    const { container } = render(<ChordChart billboard={billboard} />);
    fireEvent.click(screen.getByRole("button", { name: "Hide Alice" }));

    // Test Action
    fireEvent.click(screen.getByRole("button", { name: "Show all" }));

    // Expected Result
    expect(ribbons(container)).toHaveLength(2);
    expect(screen.queryByRole("button", { name: "Show all" })).not.toBeInTheDocument();
  });

  it("lists the flows of a node with their share", () => {
    // Test Data
    render(<ChordChart billboard={billboard} />);

    // Test Action
    fireEvent.click(screen.getByRole("button", { name: "Details for Bounty" }));

    // Expected Result
    const details = screen.getByRole("region", { name: "Details for Bounty" });
    expect(details).toHaveTextContent("← Alice");
    expect(details).toHaveTextContent("100 ISK");
    expect(details).toHaveTextContent("100.0%");
  });

  it("opens the details when an arc is clicked", () => {
    // Test Data
    render(<ChordChart billboard={billboard} />);

    // Test Action
    fireEvent.click(screen.getByText("Bob", { selector: "text" }).parentElement as Element);

    // Expected Result
    expect(screen.getByRole("region", { name: "Details for Bob" })).toHaveTextContent("→ ESS");
  });
});
