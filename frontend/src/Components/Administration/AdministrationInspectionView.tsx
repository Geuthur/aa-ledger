// React
import React from "react";

// AA Ledger
import AllianceLedger from "@/Pages/AllianceLedger";
import CharacterLedger from "@/Pages/CharacterLedger";
import CorporationLedger from "@/Pages/CorporationLedger";

interface AdministrationInspectionViewProps {
  ownerType: "character" | "corporation" | "alliance";
  ownerId: number;
  onBack: () => void;
}

export const AdministrationInspectionView: React.FC<AdministrationInspectionViewProps> = ({
  ownerType,
  ownerId,
  onBack,
}) => {
  if (ownerType === "character") {
    return <CharacterLedger characterIdOverride={ownerId} onBack={onBack} />;
  }

  if (ownerType === "alliance") {
    return <AllianceLedger allianceIdOverride={ownerId} onBack={onBack} />;
  }

  return <CorporationLedger corporationIdOverride={ownerId} onBack={onBack} />;
};
