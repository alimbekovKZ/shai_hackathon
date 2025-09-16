import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  CheckIcon as ChecklistIcon,
  BrainCircuitIcon,
  FileTextIcon,
  ZapIcon,
  ClockIcon,
  ShieldCheckIcon,
} from "lucide-react"

const features = [
  {
    icon: ChecklistIcon,
    title: "Auto Jira Integration",
    description: "Automatically create Jira tickets from action items and decisions made during meetings.",
    benefits: ["Smart task extraction", "Auto-assign to team members", "Priority detection"],
  },
  {
    icon: FileTextIcon,
    title: "Meeting Summaries",
    description: "Generate comprehensive meeting summaries with key points, decisions, and next steps.",
    benefits: ["Executive summaries", "Detailed transcripts", "Searchable archives"],
  },
  {
    icon: BrainCircuitIcon,
    title: "AI-Powered Analysis",
    description: "Advanced AI analyzes meeting content to identify patterns, sentiment, and insights.",
    benefits: ["Sentiment analysis", "Topic clustering", "Trend identification"],
  },
  {
    icon: ZapIcon,
    title: "Instant Processing",
    description: "Process meetings in minutes, not hours. Get results while the context is still fresh.",
    benefits: ["Real-time processing", "Batch operations", "API integration"],
  },
  {
    icon: ClockIcon,
    title: "Time Savings",
    description: "Save up to 80% of time spent on post-meeting administrative tasks.",
    benefits: ["Automated workflows", "Template generation", "Bulk operations"],
  },
  {
    icon: ShieldCheckIcon,
    title: "Enterprise Security",
    description: "Bank-level security with SOC2 compliance and end-to-end encryption.",
    benefits: ["Data encryption", "Access controls", "Audit trails"],
  },
]

export function FeatureHighlights() {
  return (
    <section id="features" className="py-20 px-4 bg-muted/30">
      <div className="container mx-auto max-w-6xl">
        <div className="text-center space-y-4 mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-balance">
            Everything you need to streamline your meetings
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto text-pretty">
            From AI-powered analysis to seamless integrations, we've got your meeting workflow covered.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <Card key={index} className="bg-card border-border hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                  <feature.icon className="h-6 w-6 text-primary" />
                </div>
                <CardTitle className="text-xl">{feature.title}</CardTitle>
                <CardDescription className="text-muted-foreground">{feature.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {feature.benefits.map((benefit, benefitIndex) => (
                    <li key={benefitIndex} className="flex items-center text-sm text-muted-foreground">
                      <div className="h-1.5 w-1.5 bg-accent rounded-full mr-3 flex-shrink-0" />
                      {benefit}
                    </li>
                  ))}
                </ul>
                <Button variant="ghost" className="w-full mt-4 text-primary hover:text-primary/80">
                  Learn More
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  )
}
