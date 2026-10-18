// Third Party
import { Card } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';

// Voices of War
import { ErrorLoader } from '@/Components/Base/Loader';
export function ErrorPage() {
    const { t } = useTranslation();
    return (
        <Card className="aa-panel-lg">
            <Card.Body className="p-0">
                <ErrorLoader title={t("Error 404")} message={t("The page you are looking for does not exist.")} />
            </Card.Body>
        </Card>
    );
}
