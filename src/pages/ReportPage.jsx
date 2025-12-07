import React from "react";
import { useParams, Link } from "react-router-dom";
import {
  ArrowLeft,
  ExternalLink,
  Building2,
  MapPin,
  Sparkles,
} from "lucide-react";
import api from "../services/api";

const ReportPage = () => {
  const { id } = useParams();
  const [company, setCompany] = React.useState(null);
  const [project, setProject] = React.useState(null);
  const [insights, setInsights] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);

  // Fetch data from backend
  React.useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);

        // Try to fetch as company first
        const companyResult = await api.getCompanyById(id);
        if (companyResult.success) {
          setCompany(companyResult.data);

          // Fetch insights data
          try {
            const insightsResult = await api.getCompanyInsights(id);
            if (insightsResult.success) {
              setInsights(insightsResult.data);
            }
          } catch (err) {
            console.log("Insights not available:", err);
          }
        } else {
          // Try as project
          const projectResult = await api.getProjectById(id);
          if (projectResult.success) {
            setProject(projectResult.data);
          } else {
            setError("Not found");
          }
        }
      } catch (err) {
        console.error("Error fetching report data:", err);
        setError("Failed to load data");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  const isCompany = !!company;
  const isProject = !!project;

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-green-500 mx-auto mb-4"></div>
          <p className="text-slate-400">Loading report...</p>
        </div>
      </div>
    );
  }

  if (error || (!company && !project)) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-green-400 mb-4">Not Found</h2>
          <p className="text-slate-400 mb-6">
            {error || "The requested company or project could not be found."}
          </p>
          <Link
            to="/"
            className="text-green-400 hover:text-green-300 underline"
          >
            Return to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-20 w-96 h-96 bg-green-500/10 rounded-full blur-3xl animate-float"></div>
        <div
          className="absolute bottom-20 right-20 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl animate-float"
          style={{ animationDelay: "1s" }}
        ></div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 relative z-10">
        {/* Back Button */}
        <Link
          to="/"
          className="inline-flex items-center space-x-2 text-green-400 hover:text-green-300 mb-6 transition"
        >
          <ArrowLeft className="w-5 h-5" />
          <span className="font-medium">Back to Dashboard</span>
        </Link>

        {isCompany && (
          <>
            {/* COMPANY VIEW */}
            {/* Header Section */}
            <div className="bg-gradient-to-br from-slate-900/95 via-slate-800/95 to-slate-900/95 backdrop-blur-xl rounded-2xl shadow-2xl p-8 mb-8 border border-green-500/30 animate-slideIn">
              <div className="flex justify-between items-start">
                <div>
                  <div className="flex items-center space-x-3 mb-2">
                    <Building2 className="w-10 h-10 text-green-400" />
                    <h1 className="text-4xl font-bold bg-gradient-to-r from-green-400 via-emerald-300 to-green-400 bg-clip-text text-transparent">
                      {company.name}
                    </h1>
                    <span className="bg-gradient-to-r from-green-600 to-emerald-600 text-white px-3 py-1 rounded-full text-sm font-semibold shadow-lg">
                      {company.id}
                    </span>
                  </div>
                  <p className="text-lg text-slate-400 mb-6">
                    {company.industry}
                  </p>

                  <div className="flex items-center space-x-8">
                    <div>
                      <p className="text-sm text-slate-500">Stock Price</p>
                      <p className="text-3xl font-bold text-slate-200">
                        ${company.stock_price || "N/A"}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-500">Market Cap</p>
                      <p className="text-3xl font-bold text-slate-200">
                        {company.market_cap || "N/A"}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-500">ESG Rating</p>
                      <p className="text-3xl font-bold text-green-400">
                        {company.esg_rating || "N/A"}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Main Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              {/* Left Column - Company Description */}
              <div
                className="bg-gradient-to-br from-slate-900/95 via-slate-800/95 to-slate-900/95 backdrop-blur-xl rounded-2xl shadow-2xl p-6 border border-green-500/30 animate-slideIn"
                style={{ animationDelay: "0.2s" }}
              >
                <h2 className="text-2xl font-bold text-green-400 mb-4 flex items-center gap-2">
                  <Building2 className="w-6 h-6" />
                  Company Overview
                </h2>
                <p className="text-slate-300 leading-relaxed mb-6">
                  {company.description}
                </p>

                {company.website && (
                  <a
                    href={company.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 text-green-400 hover:text-green-300 transition"
                  >
                    <ExternalLink className="w-4 h-4" />
                    <span>Visit Website</span>
                  </a>
                )}
              </div>

              {/* Right Column - AI Insights */}
              <div
                className="bg-gradient-to-br from-slate-900/95 via-slate-800/95 to-slate-900/95 backdrop-blur-xl rounded-2xl shadow-2xl p-6 border border-green-500/30 animate-slideIn"
                style={{ animationDelay: "0.3s" }}
              >
                <h2 className="text-2xl font-bold text-green-400 mb-4 flex items-center gap-2">
                  <Sparkles className="w-6 h-6" />
                  AI-Powered Insights
                </h2>
                {insights ? (
                  <div className="space-y-4">
                    <div className="p-4 bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/30 rounded-xl">
                      <h3 className="font-semibold text-green-300 mb-2">
                        Overview
                      </h3>
                      <p className="text-slate-300 text-sm leading-relaxed">
                        {insights.overview?.narrative || insights.overview}
                      </p>
                    </div>

                    <div className="p-4 bg-slate-800/50 border border-slate-700/50 rounded-xl">
                      <h3 className="font-semibold text-green-300 mb-3">
                        Sustainability Findings
                      </h3>
                      {insights.sustainability_insights?.findings?.length >
                      0 ? (
                        <ul className="space-y-3">
                          {insights.sustainability_insights.findings.map(
                            (finding, idx) => (
                              <li key={idx} className="text-slate-300 text-sm">
                                <div className="flex items-start gap-2">
                                  <span className="text-green-400 mt-1">•</span>
                                  <div>
                                    <span className="font-semibold text-green-300">
                                      {finding.title}:{" "}
                                    </span>
                                    <span>{finding.description}</span>
                                  </div>
                                </div>
                              </li>
                            )
                          )}
                        </ul>
                      ) : (
                        <p className="text-slate-400 text-sm">
                          {insights.sustainability_insights?.summary ||
                            "No sustainability findings available."}
                        </p>
                      )}
                    </div>

                    <div className="p-4 bg-gradient-to-r from-purple-500/10 to-blue-500/10 border border-purple-500/30 rounded-xl">
                      <h3 className="font-semibold text-purple-300 mb-2">
                        Future Impact
                      </h3>
                      <p className="text-slate-300 text-sm leading-relaxed mb-3">
                        {insights.future_impact_analysis?.narrative ||
                          insights.future_impact}
                      </p>
                      {insights.future_impact_analysis?.projected_impact && (
                        <div className="mt-3 pt-3 border-t border-purple-500/20">
                          <p className="text-sm text-slate-400">
                            <span className="text-purple-300 font-semibold">
                              Projected Impact:{" "}
                            </span>
                            {insights.future_impact_analysis.projected_impact}{" "}
                            over {insights.future_impact_analysis.timeframe}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="p-4 bg-slate-800/50 border border-slate-700/50 rounded-xl">
                      <p className="text-slate-400 text-sm">
                        {company.name} operates in the {company.industry} sector
                        with a market cap of {company.market_cap} and an ESG
                        rating of {company.esg_rating}.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </>
        )}

        {isProject && (
          <>
            {/* PROJECT VIEW */}
            {/* Header Section */}
            <div className="bg-gradient-to-br from-slate-900/95 via-slate-800/95 to-slate-900/95 backdrop-blur-xl rounded-2xl shadow-2xl p-8 mb-8 border border-green-500/30 animate-slideIn">
              <div className="flex justify-between items-start">
                <div>
                  <div className="flex items-center space-x-3 mb-2">
                    <h1 className="text-4xl font-bold bg-gradient-to-r from-green-400 via-emerald-300 to-green-400 bg-clip-text text-transparent">
                      {project.name || project.project_name || "Project"}
                    </h1>
                    <span className="bg-gradient-to-r from-green-600 to-emerald-600 text-white px-3 py-1 rounded-full text-sm font-semibold shadow-lg">
                      {project.id || "N/A"}
                    </span>
                  </div>

                  <div className="flex items-center gap-6 mt-4">
                    <div className="flex items-center gap-2 text-slate-400">
                      <span className="px-3 py-1 bg-green-500/20 text-green-300 rounded-lg border border-green-500/30 text-sm font-semibold">
                        {project.category || "Uncategorized"}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-400">
                      <MapPin className="w-5 h-5 text-green-400" />
                      <span className="text-lg">
                        {project.country || "Unknown"}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Main Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Details Card */}
              <div
                className="lg:col-span-2 bg-gradient-to-br from-slate-900/95 via-slate-800/95 to-slate-900/95 backdrop-blur-xl rounded-2xl shadow-2xl p-6 border border-green-500/30 animate-slideIn"
                style={{ animationDelay: "0.1s" }}
              >
                <h2 className="text-2xl font-bold text-green-400 mb-6 flex items-center gap-2">
                  <Sparkles className="w-6 h-6" />
                  {project.has_ai_report
                    ? "AI-Generated Project Report"
                    : "Project Details"}
                </h2>

                {project.image_url && (
                  <img
                    src={project.image_url}
                    alt={project.name}
                    className="w-full h-64 object-cover rounded-xl mb-6 border border-green-500/20"
                  />
                )}

                <div className="space-y-6">
                  {/* AI-Generated Report */}
                  {project.ai_report && (
                    <div className="prose prose-invert prose-green max-w-none">
                      <div className="text-slate-300 leading-relaxed space-y-4">
                        {project.ai_report.split("\n").map((line, idx) => {
                          const trimmed = line.trim();

                          // Skip empty lines
                          if (!trimmed) {
                            return <div key={idx} className="h-2"></div>;
                          }

                          // Parse bold text helper function
                          const parseBold = (text) => {
                            const parts = text.split(/(\*\*.*?\*\*)/g);
                            return parts.map((part, i) => {
                              if (
                                part.startsWith("**") &&
                                part.endsWith("**")
                              ) {
                                const content = part.slice(2, -2);
                                return (
                                  <strong
                                    key={i}
                                    className="text-green-300 font-bold"
                                  >
                                    {content}
                                  </strong>
                                );
                              }
                              return <span key={i}>{part}</span>;
                            });
                          };

                          // Headers
                          if (trimmed.startsWith("# ")) {
                            return (
                              <h1
                                key={idx}
                                className="text-3xl font-bold text-green-400 mt-8 mb-4"
                              >
                                {trimmed.slice(2)}
                              </h1>
                            );
                          }
                          if (trimmed.startsWith("## ")) {
                            return (
                              <h2
                                key={idx}
                                className="text-2xl font-bold text-green-300 mt-6 mb-3"
                              >
                                {trimmed.slice(3)}
                              </h2>
                            );
                          }
                          if (trimmed.startsWith("### ")) {
                            return (
                              <h3
                                key={idx}
                                className="text-xl font-semibold text-green-200 mt-5 mb-2"
                              >
                                {trimmed.slice(4)}
                              </h3>
                            );
                          }
                          if (trimmed.startsWith("#### ")) {
                            return (
                              <h4
                                key={idx}
                                className="text-lg font-semibold text-green-100 mt-4 mb-2"
                              >
                                {trimmed.slice(5)}
                              </h4>
                            );
                          }

                          // Bullet points
                          if (
                            trimmed.startsWith("- ") ||
                            trimmed.startsWith("* ")
                          ) {
                            const content = trimmed.slice(2);
                            return (
                              <li
                                key={idx}
                                className="text-slate-300 ml-6 mb-2 leading-relaxed"
                              >
                                {parseBold(content)}
                              </li>
                            );
                          }

                          // Numbered lists
                          if (/^\d+\.\s/.test(trimmed)) {
                            const content = trimmed.replace(/^\d+\.\s/, "");
                            return (
                              <li
                                key={idx}
                                className="text-slate-300 ml-6 mb-2 leading-relaxed list-decimal"
                              >
                                {parseBold(content)}
                              </li>
                            );
                          }

                          // Regular paragraphs with bold text support
                          return (
                            <p
                              key={idx}
                              className="text-slate-300 leading-relaxed mb-3"
                            >
                              {parseBold(trimmed)}
                            </p>
                          );
                        })}
                      </div>
                      <div className="mt-6 p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
                        <p className="text-xs text-green-300 flex items-center gap-2">
                          <Sparkles className="w-4 h-4" />
                          This report was generated by AI using project data
                          from Verra Registry
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Fallback if no AI report */}
                  {!project.ai_report && (
                    <>
                      <div>
                        <h3 className="text-lg font-semibold text-green-300 mb-2">
                          Description
                        </h3>
                        <p className="text-slate-300 leading-relaxed">
                          {project.description || "No description available."}
                        </p>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div className="p-4 bg-slate-800/50 border border-slate-700/50 rounded-xl">
                          <p className="text-sm text-slate-500 mb-1">
                            Methodology
                          </p>
                          <p className="text-lg font-semibold text-slate-200">
                            {project.methodology || "N/A"}
                          </p>
                        </div>
                        <div className="p-4 bg-slate-800/50 border border-slate-700/50 rounded-xl">
                          <p className="text-sm text-slate-500 mb-1">Vintage</p>
                          <p className="text-lg font-semibold text-slate-200">
                            {project.vintage || "N/A"}
                          </p>
                        </div>
                        <div className="p-4 bg-slate-800/50 border border-slate-700/50 rounded-xl">
                          <p className="text-sm text-slate-500 mb-1">Country</p>
                          <p className="text-lg font-semibold text-slate-200">
                            {project.country || "Unknown"}
                          </p>
                        </div>
                        <div className="p-4 bg-slate-800/50 border border-slate-700/50 rounded-xl">
                          <p className="text-sm text-slate-500 mb-1">
                            Category
                          </p>
                          <p className="text-lg font-semibold text-slate-200">
                            {project.category || "Uncategorized"}
                          </p>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* Market Data & Actions */}
              <div className="space-y-6">
                {/* Market Data */}
                <div
                  className="bg-gradient-to-br from-slate-900/95 via-slate-800/95 to-slate-900/95 backdrop-blur-xl rounded-2xl shadow-2xl p-6 border border-green-500/30 animate-slideIn"
                  style={{ animationDelay: "0.2s" }}
                >
                  <h2 className="text-xl font-bold text-green-400 mb-4">
                    Market Data
                  </h2>

                  <div className="space-y-4">
                    <div className="p-4 bg-gradient-to-r from-green-500/20 to-emerald-500/20 border border-green-500/40 rounded-xl">
                      <p className="text-sm text-slate-400 mb-1">
                        Price per Credit
                      </p>
                      <p className="text-4xl font-bold text-green-400">
                        ${project.price || "N/A"}
                      </p>
                    </div>

                    <div className="p-4 bg-slate-800/50 border border-slate-700/50 rounded-xl">
                      <p className="text-sm text-slate-400 mb-1">
                        Available Credits
                      </p>
                      <p className="text-2xl font-bold text-slate-200">
                        {project.available_credits
                          ? project.available_credits.toLocaleString()
                          : "N/A"}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ReportPage;
