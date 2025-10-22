import type React from "react"
import { CheckCircle, Clock, AlertCircle } from "lucide-react"

interface StreamEvent {
  type: string
  step: string
  message: string
  reasoning?: string
  progress?: number
}

interface ExecutionLogTableProps {
  events: StreamEvent[]
  isStreaming: boolean
}

export const ExecutionLogTable: React.FC<ExecutionLogTableProps> = ({ events, isStreaming }) => {
  const getStepIcon = (step: string) => {
    if (step === "new_query") {
      return <Clock className="w-4 h-4 text-blue-500" />
    }
    if (step.includes("error") || step.includes("failed")) {
      return <AlertCircle className="w-4 h-4 text-red-500" />
    }
    return <CheckCircle className="w-4 h-4 text-green-500" />
  }

  const getStepLabel = (step: string) => {
    return step
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ")
  }

  const displayEvents = events.slice(-10) // Show last 10 events

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border">
            <th className="text-left py-2 px-3 font-semibold text-muted-foreground">Step</th>
            <th className="text-left py-2 px-3 font-semibold text-muted-foreground">Message</th>
            <th className="text-left py-2 px-3 font-semibold text-muted-foreground">Progress</th>
          </tr>
        </thead>
        <tbody>
          {displayEvents.map((event, idx) => (
            <tr key={idx} className="border-b border-border/50 hover:bg-muted/50 transition-colors">
              <td className="py-2 px-3">
                <div className="flex items-center gap-2">
                  {getStepIcon(event.step)}
                  <span className="text-xs font-medium text-foreground">{getStepLabel(event.step)}</span>
                </div>
              </td>
              <td className="py-2 px-3">
                <div className="flex flex-col gap-1">
                  <span className="text-foreground">{event.message}</span>
                  {event.reasoning && <span className="text-xs text-muted-foreground italic">{event.reasoning}</span>}
                </div>
              </td>
              <td className="py-2 px-3">
                {event.progress !== undefined && (
                  <div className="flex items-center gap-2">
                    <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                      <div className="h-full bg-primary transition-all" style={{ width: `${event.progress}%` }} />
                    </div>
                    <span className="text-xs text-muted-foreground">{event.progress}%</span>
                  </div>
                )}
              </td>
            </tr>
          ))}
          {isStreaming && (
            <tr className="border-b border-border/50">
              <td colSpan={3} className="py-2 px-3">
                <div className="flex items-center gap-2">
                  <div className="flex gap-1">
                    <div className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce" />
                    <div
                      className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce"
                      style={{ animationDelay: "0.1s" }}
                    />
                    <div
                      className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce"
                      style={{ animationDelay: "0.2s" }}
                    />
                  </div>
                  <span className="text-xs text-muted-foreground">Processing...</span>
                </div>
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
