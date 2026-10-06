// Third Party
import { useTranslation } from 'react-i18next';

// Voices of War
import { ErrorLoader } from '@/Components/Base/Loader';
export function ErrorPage() {
    const { t } = useTranslation();
    return (
        <main className="aa-panel-lg">
            <ErrorLoader title={t("Error 404")} message={t("The page you are looking for does not exist.")} />
        </main>
    );
}
