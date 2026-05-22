export type FamilyInvite = {
  id: number;
  family_id: number;
  status: string;
  invite_token: string;
  invited_phone_masked: string;
  invited_user_id: number | null;
  share_url: string;
  share_text: string;
  deep_link: string;
  invitee_notified: boolean;
  is_link_invite: boolean;
  family_name: string;
  created_at: string;
};
