// React
import { useMemo, useState } from "react";

// Third Party
import { Search, Shield } from "lucide-react";
import { Badge, Card, Col, Form, InputGroup, Row, Spinner } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA Ledger
import BaseSectionHeader from "@/Components/Base/BaseHeader";
import { OverviewOwnerCard, OwnerTypeFilter } from "@/Components/Overview";
import { useOverview } from "@/Components/Overview/Hooks";

export function OverviewPage() {
  const { t } = useTranslation();
  const [search, setSearch] = useState("");
  const [ownerType, setOwnerType] = useState("all");

  const { data, isLoading, isError, error } = useOverview();

  const filteredOwners = useMemo(() => {
    if (!data?.owners) return [];
    return data.owners.filter((owner) => {
      const q = search.trim().toLowerCase();
      const matchesSearch =
        !q ||
        owner.name.toLowerCase().includes(q) ||
        (owner.subtitle && owner.subtitle.toLowerCase().includes(q));
      const matchesType = ownerType === "all" || owner.type === ownerType;
      return matchesSearch && matchesType;
    });
  }, [data, search, ownerType]);

  return (
    <Card className="border-0 bg-dark-body">
      <Card.Body>
        <BaseSectionHeader name={t("Ledger Overview")}>
          <div className="d-flex align-items-center gap-2">
            <Badge bg="secondary" className="px-3 py-2">
              {filteredOwners.length} {t("Owners")}
            </Badge>
          </div>
        </BaseSectionHeader>

        <div className="bg-dark card-body rounded">
          <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-4">
            <div className="d-flex flex-wrap align-items-center gap-2 m-2">
              <InputGroup className="lg-overview-search">
                <InputGroup.Text className="bg-body border-secondary text-secondary">
                  <Search size={16} />
                </InputGroup.Text>
                <Form.Control
                  type="text"
                  placeholder={t("Search characters, corporations & alliances…")}
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="bg-body text-light border-secondary"
                />
              </InputGroup>

              <OwnerTypeFilter
                ownerType={ownerType}
                setOwnerType={setOwnerType}
                t={t}
              />
            </div>
          </div>

          {isLoading && (
            <div className="text-center py-5">
              <Spinner animation="border" variant="primary" />
              <div className="mt-2 text-muted">{t("Loading ledger owners…")}</div>
            </div>
          )}

          {isError && (
            <div className="alert alert-danger" role="alert">
              {error instanceof Error ? error.message : t("Failed to load overview")}
            </div>
          )}

          {!isLoading && !isError && filteredOwners.length === 0 && (
            <div className="text-center py-5 text-muted">
              <Shield size={48} className="mb-3 opacity-50" />
              <h5>{t("No ledger owners found")}</h5>
              <p className="small">
                {t("No owners match your search query or filter.")}
              </p>
            </div>
          )}

          <Row className="g-3">
            {filteredOwners.map((owner) => (
              <Col key={`${owner.type}-${owner.id}`} xs={12} md={6} lg={4}>
                <OverviewOwnerCard owner={owner} />
              </Col>
            ))}
          </Row>
        </div>
      </Card.Body>
    </Card>
  );
}

export default OverviewPage;
