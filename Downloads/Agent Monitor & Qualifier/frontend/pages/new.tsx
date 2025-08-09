
import React, { useState } from "react";
const PACKS = ["functional","safety","determinism","compliance","tool_robustness"] as const;

// ...existing code...

export default function NewRunPage() {
  // ...existing code...
  // cho state should be initialized with all true for all packs
  const [cho, setCho] = useState(() => Object.fromEntries(PACKS.map(p => [p, true])));
  // ...existing code...
}
