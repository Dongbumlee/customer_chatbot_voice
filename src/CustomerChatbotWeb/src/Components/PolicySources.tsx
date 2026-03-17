/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

interface PolicySource {
  name: string;
  reference?: string;
}

interface PolicySourcesProps {
  sources: PolicySource[];
}

/**
 * Displays policy source citations when the Policy Agent responds.
 */
export function PolicySources({ sources }: PolicySourcesProps) {
  if (sources.length === 0) return null;

  return (
    <div className="policy-sources">
      <span className="policy-sources__label">📎 Sources:</span>
      <ul className="policy-sources__list">
        {sources.map((source, index) => (
          <li key={index} className="policy-sources__item">
            {source.name}
            {source.reference && (
              <span className="policy-sources__ref"> — {source.reference}</span>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
