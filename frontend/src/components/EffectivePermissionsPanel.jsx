/**
 * EffectivePermissionsPanel — Categorized view of resolved effective system permissions.
 */

export function EffectivePermissionsPanel({ permissions = [] }) {
  // Domain groupings for canonical permissions
  const domainGroups = [
    {
      domain: "Books & Catalog",
      icon: "📚",
      color: "indigo",
      prefixes: ["book:"],
    },
    {
      domain: "Circulation & Loans",
      icon: "📖",
      color: "blue",
      prefixes: ["borrow:"],
    },
    {
      domain: "User Management",
      icon: "👥",
      color: "purple",
      prefixes: ["user:"],
    },
    {
      domain: "Roles & RBAC",
      icon: "🛡️",
      color: "amber",
      prefixes: ["role:"],
    },
    {
      domain: "Permission Assignment",
      icon: "🔑",
      color: "emerald",
      prefixes: ["permission:"],
    },
    {
      domain: "Security & Auditing",
      icon: "📋",
      color: "rose",
      prefixes: ["audit_log:"],
    },
  ];

  const categorized = domainGroups.map((group) => {
    const matched = permissions.filter((perm) =>
      group.prefixes.some((prefix) => perm.toLowerCase().startsWith(prefix))
    );
    return {
      ...group,
      permissions: matched,
    };
  });

  const otherPermissions = permissions.filter((perm) => {
    return !domainGroups.some((group) =>
      group.prefixes.some((prefix) => perm.toLowerCase().startsWith(prefix))
    );
  });

  return (
    <div className="rounded-2xl border border-gray-800 bg-gray-900/40 p-6 text-left space-y-5">
      <div className="flex items-center justify-between border-b border-gray-800 pb-3">
        <div className="flex items-center gap-2">
          <span className="text-lg">🔑</span>
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Effective Permissions Resolution
            </h3>
            <p className="text-[11px] text-gray-400">
              Derived automatically from assigned RBAC roles via database mappings
            </p>
          </div>
        </div>
        <span className="rounded-full bg-indigo-950/80 border border-indigo-500/40 px-2.5 py-0.5 text-xs font-mono font-bold text-indigo-300">
          {permissions.length} Active
        </span>
      </div>

      {permissions.length === 0 ? (
        <p className="text-xs text-gray-400 py-4 text-center">
          No effective system permissions assigned to this user account.
        </p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {categorized.map((group) => (
            <div
              key={group.domain}
              className={`rounded-xl border border-gray-800 bg-gray-950/50 p-4 space-y-2.5 ${
                group.permissions.length === 0 ? "border-dashed" : ""
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-gray-300 flex items-center gap-1.5">
                  <span>{group.icon}</span> {group.domain}
                </span>
                <span className="text-[10px] font-mono text-gray-400">
                  {group.permissions.length}
                </span>
              </div>

              {group.permissions.length === 0 ? (
                <p className="text-[11px] text-gray-400 font-medium italic">None granted</p>
              ) : (
                <div className="flex flex-wrap gap-1.5">
                  {group.permissions.map((perm) => (
                    <span
                      key={perm}
                      className="font-mono text-[11px] px-2 py-0.5 rounded-md bg-gray-800/90 border border-gray-700/60 text-indigo-300"
                    >
                      {perm}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}

          {otherPermissions.length > 0 && (
            <div className="rounded-xl border border-gray-800 bg-gray-950/50 p-4 space-y-2.5">
              <span className="text-xs font-bold text-gray-300">Other Permissions</span>
              <div className="flex flex-wrap gap-1.5">
                {otherPermissions.map((perm) => (
                  <span
                    key={perm}
                    className="font-mono text-[11px] px-2 py-0.5 rounded-md bg-gray-800/90 border border-gray-700/60 text-gray-300"
                  >
                    {perm}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default EffectivePermissionsPanel;
