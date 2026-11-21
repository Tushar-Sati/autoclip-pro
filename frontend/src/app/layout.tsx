import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AutoClip Pro | AI YouTube Video & Stream Clipper",
  description: "Autonomous AI clipping tool: converts long YouTube videos and live streams into viral 9:16 Shorts with gaming split-screen, Hormozi captions, and virality scoring.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-background text-gray-100 min-h-screen">{children}</body>
    </html>
  );
}
