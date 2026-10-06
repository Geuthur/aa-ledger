// React
import { useState } from 'react';

// Third Party
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import { useTranslation } from 'react-i18next';

interface UserSettingsFormProps {
    initialDisableNotifications: boolean;
    onSubmit: (disableNotifications: boolean) => void;
    isPending?: boolean;
}

/**
 * Form for managing user settings (notifications).
 */
export default function UserSettingsForm({
    initialDisableNotifications,
    onSubmit,
    isPending = false,
}: UserSettingsFormProps) {
    const { t } = useTranslation();
    const [disableNotifications, setDisableNotifications] = useState<boolean>(initialDisableNotifications);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSubmit(disableNotifications);
    };

    return (
        <Form onSubmit={handleSubmit}>
            <Form.Group controlId="disable_notifications" className="mb-3">
                <Form.Check
                    type="checkbox"
                    id="disable_notifications"
                    label={t("Disable Notifications")}
                    checked={disableNotifications}
                    onChange={(e) => setDisableNotifications(e.target.checked)}
                />
                <Form.Text className="text-muted d-block">
                    {t("Check this box to disable notifications for expired belt timers.")}
                </Form.Text>
            </Form.Group>

            <div className="text-end">
                <Button type="submit" variant="primary" disabled={isPending}>
                    {isPending ? t("Saving...") : t("Save Settings")}
                </Button>
            </div>
        </Form>
    );
}
