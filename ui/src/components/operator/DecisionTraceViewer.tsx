import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { fetchUsers } from '../../services/api'
import { fetchUserTraces, DecisionTrace } from '../../services/operatorApi'
import { AlertCircle, FileText, Clock } from 'lucide-react'

export default function DecisionTraceViewer() {
  const [selectedUserId, setSelectedUserId] = useState<string>('')

  const { data: users } = useQuery({
    queryKey: ['users'],
    queryFn: fetchUsers,
  })

  const { data: tracesData, isLoading, error } = useQuery({
    queryKey: ['operator-traces', selectedUserId],
    queryFn: () => fetchUserTraces(selectedUserId),
    enabled: !!selectedUserId,
  })

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-6 py-4 border-b border-[#D4C4B0]">
        <h2 className="text-lg font-semibold text-[#5D4037]">Decision Trace Viewer</h2>
        <p className="text-sm text-[#556B2F] mt-1">
          View decision traces for persona assignment decisions
        </p>
      </div>

      <div className="px-6 py-4 space-y-4">
        <div>
          <label className="block text-sm font-medium text-[#556B2F] mb-2">Select User</label>
          <select
            value={selectedUserId}
            onChange={(e) => setSelectedUserId(e.target.value)}
            className="w-full px-3 py-2 border border-[#D4C4B0] rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-[#556B2F]"
          >
            <option value="">-- Select a user --</option>
            {users?.map((user: any) => (
              <option key={user.id} value={user.id}>
                {user.name} ({user.email})
              </option>
            ))}
          </select>
        </div>

        {!selectedUserId && (
          <div className="text-center py-12 text-[#8B6F47]">
            <AlertCircle className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <p>Please select a user to view their decision traces</p>
          </div>
        )}

        {selectedUserId && isLoading && (
          <div className="text-center py-12 text-[#8B6F47]">Loading traces...</div>
        )}

        {selectedUserId && error && (
          <div className="text-center py-12 text-red-600">
            Error loading traces: {(error as Error).message}
          </div>
        )}

        {selectedUserId && tracesData && (
          <div className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
              <p className="text-sm font-medium text-blue-900">
                Found {tracesData.total} decision trace(s) for user {tracesData.user_id}
              </p>
            </div>

            {tracesData.traces.length === 0 ? (
              <div className="text-center py-12 text-[#8B6F47]">
                <FileText className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p>No decision traces found for this user</p>
                <p className="text-sm mt-2">
                  Traces are created when persona assignments are made. Make sure persona assignment has been run for this user.
                </p>
              </div>
            ) : (
              tracesData.traces.map((trace: DecisionTrace, index: number) => (
                <TraceCard key={index} trace={trace} />
              ))
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function TraceCard({ trace }: { trace: DecisionTrace }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="border border-[#D4C4B0] rounded-lg">
      <div
        className="px-4 py-3 bg-[#E8F5E9] border-b border-[#D4C4B0] cursor-pointer hover:bg-[#F5E6D3]"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <FileText className="h-5 w-5 text-[#8B6F47]" />
            <div>
              <h3 className="text-md font-semibold text-[#5D4037]">
                Primary Persona: {trace.primary_persona}
              </h3>
              <p className="text-sm text-[#556B2F]">
                <Clock className="h-3 w-3 inline mr-1" />
                {new Date(trace.timestamp).toLocaleString()}
              </p>
            </div>
          </div>
          <div className="text-sm text-[#8B6F47]">
            {expanded ? '▼' : '▶'}
          </div>
        </div>
      </div>

      {expanded && (
        <div className="p-4 space-y-4">
          <div>
            <h4 className="text-sm font-medium text-[#5D4037] mb-2">Assigned Personas</h4>
            <div className="flex flex-wrap gap-2">
              {trace.assigned_personas.map((persona, idx) => (
                <span
                  key={idx}
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    persona === trace.primary_persona
                      ? 'bg-[#E8F5E9] text-[#5D4037]'
                      : 'bg-[#F5E6D3] text-[#5D4037]'
                  }`}
                >
                  {persona}
                </span>
              ))}
            </div>
          </div>

          <div>
            <h4 className="text-sm font-medium text-[#5D4037] mb-2">Matching Results</h4>
            <div className="bg-[#E8F5E9] rounded-md p-3 space-y-2">
              {Object.entries(trace.matching_results).map(([personaId, result]: [string, any]) => (
                <div key={personaId} className="border-b border-[#D4C4B0] pb-2 last:border-0 last:pb-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-sm text-[#5D4037]">{personaId}:</span>
                    {result.matched ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                        ✓ Matched
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-[#F5E6D3] text-[#5D4037]">
                        ✗ Not Matched
                      </span>
                    )}
                  </div>
                  {result.reasons && result.reasons.length > 0 && (
                    <ul className="list-disc list-inside text-xs text-[#556B2F] ml-4">
                      {result.reasons.map((reason: string, idx: number) => (
                        <li key={idx}>{reason}</li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div>
            <h4 className="text-sm font-medium text-[#5D4037] mb-2">Rationale</h4>
            <p className="text-sm text-[#556B2F] bg-blue-50 rounded-md p-3">{trace.rationale}</p>
          </div>

          <details className="mt-4">
            <summary className="text-sm font-medium text-[#556B2F] cursor-pointer hover:text-[#5D4037]">
              View Features Snapshot
            </summary>
            <div className="mt-2 bg-[#E8F5E9] rounded-md p-3">
              <pre className="text-xs text-[#556B2F] overflow-auto">
                {JSON.stringify(trace.features_snapshot, null, 2)}
              </pre>
            </div>
          </details>
        </div>
      )}
    </div>
  )
}




