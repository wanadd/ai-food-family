"use client";

import { useEffect } from "react";

import { captureAdminSessionFromUrl } from "@/lib/admin/session";

export function AdminSessionCapture() {
  useEffect(() => {
    captureAdminSessionFromUrl();
  }, []);
  return null;
}
