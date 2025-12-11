import React from "react";
import { useParams, Link } from "react-router-dom";
import {
  ArrowLeft,
  ExternalLink,
  Building2,
  MapPin,
  Sparkles,
  TrendingUp,
  MessageCircle,
  Send,
  Award,
  FileText,
} from "lucide-react";
import api from "../services/api";

const ReportPage = () => {
  const { id } = useParams();
  
  // Company state
  const [company, setCompany] = React.useState(null);
  const [companyInsights, setCompanyInsights] = React.useState(null);
  const [companyFutureImpact, setCompanyFutureImpact] = React.useState(null);
  
  // Project state  
  const [project, setProject] = React.useState(null);
  const [projectReport, setProjectReport] = React.useState(null);
  const [reportLoading, setReportLoading] = React.useState(false);
  
  // Chat state (common)
  const [chatMessages, setChatMessages] = React.useState([]);
  const [chatInput, setChatInput] = React.useState("");
  const [chatLoading, setChatLoading] = React.useState(false);
  
  // Loading/error state
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  
  // Progress tracking state
  const [progressSteps, setProgressSteps] = React.useState([]);
  const [currentProgress, setCurrentProgress] = React.useState(null);

  // Setup WebSocket listener for progress updates
  React.useEffect(() => {
    const socket = api.initWebSocket();
    
    api.onDataUpdate('report_progress', (data) => {
      if (data.id === id) {
        setCurrentProgress(data.message);
        if (data.step) {
          setProgressSteps(prev => {
            const existing = prev.find(s => s.step === data.step);
            if (existing) return prev;
            return [...prev, { step: data.step, message: data.message, timestamp: Date.now() }];
          });
        }
      }
    });
    
    return () => {
      api.onDataUpdate('report_progress', null);
    };
  }, [id]);

  // Fetch data from backend
  React.useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setProgressSteps([]);
        setCurrentProgress(null);

        // Try to fetch as company first
        const companyResult = await api.getCompanyById(id);
        if (companyResult.success) {
          setCompany(companyResult.data);

          // Fetch company insights (Section 2)
          try {
            setProgressSteps([{ step: 1, message: 'Fetching company insights...', timestamp: Date.now() }]);
            setCurrentProgress('Fetching company insights...');
            const insightsResult = await api.getCompanyInsights(id);
            if (insightsResult.success) {
              setCompanyInsights(insightsResult.data);
              setProgressSteps(prev => [...prev, { step: 2, message: 'Company insights loaded', timestamp: Date.now() }]);
            }
          } catch (err) {
            console.log("Company insights not available:", err);
          }

          // Fetch future impact (Section 3)
          try {
            setCurrentProgress('Analyzing future impact...');
            setProgressSteps(prev => [...prev, { step: 3, message: 'Analyzing sustainability & future impact...', timestamp: Date.now() }]);
            const futureResult = await api.getFutureImpactAnalysis(id);
            if (futureResult.success) {
              setCompanyFutureImpact(futureResult.data);
              setProgressSteps(prev => [...prev, { step: 4, message: 'Analysis complete', timestamp: Date.now() }]);
              setCurrentProgress(null);
            }
          } catch (err) {
            console.log("Future impact not available:", err);
            setCurrentProgress(null);
          }
        } else {
          // Try as project
          const projectResult = await api.getProjectById(id);
          if (projectResult.success) {
            setProject(projectResult.data);
            
            // Fetch project report (Section 2)
            setReportLoading(true);
            setProgressSteps([{ step: 1, message: 'Generating comprehensive project report...', timestamp: Date.now() }]);
            setCurrentProgress('Generating comprehensive project report...');
            try {
              const reportResult = await api.getProjectReport(id);
              if (reportResult.success) {
                setProjectReport(reportResult.data);
                setProgressSteps(prev => [...prev, { step: 2, message: 'Report generation complete', timestamp: Date.now() }]);
                setCurrentProgress(null);
              }
            } catch (err) {
              console.log("Project report not available:", err);
              setCurrentProgress(null);
            } finally {
              setReportLoading(false);
            }
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

  const handleSendMessage = async () => {
    if (!chatInput.trim() || chatLoading) return;

    const userMessage = chatInput.trim();
    setChatInput("");

    // Add user message to chat
    setChatMessages((prev) => [
      ...prev,
      { role: "user", content: userMessage },
    ]);

    setChatLoading(true);

    try {
      let result;
      if (company) {
        result = await api.askCompanyQuestion(id, userMessage);
      } else if (project) {
        result = await api.askProjectQuestion(id, userMessage);
      }
      
      if (result.success) {
        setChatMessages((prev) => [
          ...prev,
          { role: "assistant", content: result.data.answer },
        ]);
      } else {
        setChatMessages((prev) => [
          ...prev,
          { role: "assistant", content: "Sorry, I couldn't process your question. Please try again." },
        ]);
      }
    } catch (err) {
      console.error("Chat error:", err);
      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", content: "An error occurred. Please try again later." },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

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
            {error || "The requested item could not be found."}
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
      {/* Animated background */}
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
          to={company ? "/" : "/projects"}
          className="inline-flex items-center space-x-2 text-green-400 hover:text-green-300 mb-6 transition"
        >
          <ArrowLeft className="w-5 h-5" />
          <span className="font-medium">Back to {company ? "Dashboard" : "Projects"}</span>
        </Link>

        {/* COMPANY VIEW */}
        {company && (
          <>
            {/* SECTION 1: Basic Company Info */}
            <div className="bg-gradient-to-br from-slate-900/95 via-slate-800/95 to-slate-900/95 backdrop-blur-xl rounded-2xl shadow-2xl p-8 mb-8 border border-green-500/30 animate-slideIn">
              <div className="flex items-center space-x-3 mb-2">
                <Building2 className="w-10 h-10 text-green-400" />
                <h1 className="text-4xl font-bold bg-gradient-to-r from-green-400 via-emerald-300 to-green-400 bg-clip-text text-transparent">
                  {company.name}
                </h1>
                <span className="bg-gradient-to-r from-green-600 to-emerald-600 text-white px-3 py-1 rounded-full text-sm font-semibold shadow-lg">
                  {company.ticker}
                </span>
              </div>
              <p className="text-lg text-slate-400 mb-6">{company.industry}</p>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-6">
                <div>
                  <p className="text-sm text-slate-500">Stock Price</p>
                  <p className="text-2xl font-bold text-slate-200">
                    ${company.stock_price || "N/A"}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Market Cap</p>
                  <p className="text-2xl font-bold text-slate-200">
                    {company.market_cap || "N/A"}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">ESG Rating</p>
                  <p className="text-2xl font-bold text-green-400">
                    {company.esg_rating || "N/A"}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">GII Score</p>
                  <p className="text-2xl font-bold text-emerald-400">
                    {company.gii_score || "N/A"}/100
                  </p>
                </div>
              </div>

              <div className="pt-6 border-t border-slate-700">
                <p className="text-slate-300 leading-relaxed mb-4">
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
            </div>

            {/* SECTION 2: General Insights */}
            <div
              className="bg-gradient-to-br from-slate-900/95 via-slate-800/95 to-slate-900/95 backdrop-blur-xl rounded-2xl shadow-2xl p-8 mb-8 border border-green-500/30 animate-slideIn"
              style={{ animationDelay: "0.1s" }}
            >
              <h2 className="text-2xl font-bold text-green-400 mb-6 flex items-center gap-2">
                <Sparkles className="w-6 h-6" />
                General Insights
              </h2>
              {companyInsights ? (
                <div className="prose prose-invert prose-green max-w-none">
                  <div 
                    className="text-slate-300 leading-relaxed"
                    dangerouslySetInnerHTML={{ __html: companyInsights.insights || "No insights available." }}
                  />
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-500 mx-auto mb-3"></div>
                  {currentProgress && progressSteps.length > 0 && progressSteps.some(s => s.step <= 2) && (
                    <div className="text-center mt-4">
                      <p className="text-green-400 font-medium mb-2">{currentProgress}</p>
                      <div className="space-y-1 text-sm text-slate-400">
                        {progressSteps.map((step, idx) => (
                          <div key={idx} className="flex items-center gap-2 justify-center">
                            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                            <span>{step.message}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* SECTION 3: Future Impact */}
            <div
              className="bg-gradient-to-br from-slate-900/95 via-slate-800/95 to-slate-900/95 backdrop-blur-xl rounded-2xl shadow-2xl p-8 mb-8 border border-purple-500/30 animate-slideIn"
              style={{ animationDelay: "0.2s" }}
            >
              <h2 className="text-2xl font-bold text-purple-400 mb-6 flex items-center gap-2">
                <TrendingUp className="w-6 h-6" />
                Sustainability & Future Impact
              </h2>
              {companyFutureImpact ? (
                <div className="prose prose-invert prose-purple max-w-none">
                  <div 
                    className="text-slate-300 leading-relaxed"
                    dangerouslySetInnerHTML={{ __html: companyFutureImpact.analysis || "No analysis available." }}
                  />
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500 mx-auto mb-3"></div>
                  {currentProgress && progressSteps.length > 0 && progressSteps.some(s => s.step >= 3) && (
                    <div className="text-center mt-4">
                      <p className="text-purple-400 font-medium mb-2">{currentProgress}</p>
                      <div className="space-y-1 text-sm text-slate-400">
                        {progressSteps.filter(s => s.step >= 3).map((step, idx) => (
                          <div key={idx} className="flex items-center gap-2 justify-center">
                            <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                            <span>{step.message}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </>
        )}

        {/* PROJECT VIEW */}
        {project && (
          <>
            {/* SECTION 1: Project Details */}
            <div className="bg-gradient-to-br from-slate-900/95 via-slate-800/95 to-slate-900/95 backdrop-blur-xl rounded-2xl shadow-2xl p-8 mb-8 border border-green-500/30 animate-slideIn">
              <div className="flex items-start gap-6">
                {project.image_url && (
                  <img
                    src={project.image_url}
                    alt={project.name}
                    className="w-32 h-32 object-cover rounded-xl border border-green-500/30"
                  />
                )}
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <Award className="w-10 h-10 text-green-400" />
                    <h1 className="text-4xl font-bold bg-gradient-to-r from-green-400 via-emerald-300 to-green-400 bg-clip-text text-transparent">
                      {project.name}
                    </h1>
                  </div>
                  <div className="flex items-center gap-3 mb-4">
                    <span className="bg-green-500/20 text-green-300 px-3 py-1 rounded-full text-sm border border-green-500/30">
                      {project.category}
                    </span>
                    <span className="flex items-center gap-1 text-slate-400">
                      <MapPin className="w-4 h-4" />
                      {project.country}
                    </span>
                    <span className="text-slate-500">ID: {project.project_id}</span>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-6">
                    <div>
                      <p className="text-sm text-slate-500">Available Credits</p>
                      <p className="text-2xl font-bold text-green-400">
                        {project.available_credits?.toLocaleString() || 0}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-500">Price per Credit</p>
                      <p className="text-2xl font-bold text-emerald-400">
                        ${project.price || 0}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-500">Vintage Year</p>
                      <p className="text-2xl font-bold text-slate-200">
                        {project.vintage || "N/A"}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-500">Registry Status</p>
                      <p className="text-2xl font-bold text-blue-400">
                        {project.registry_status || "Active"}
                      </p>
                    </div>
                  </div>

                  <div className="pt-6 border-t border-slate-700">
                    <p className="text-sm text-slate-500 mb-2">Methodology</p>
                    <p className="text-slate-300 mb-4">{project.methodology || "N/A"}</p>
                    
                    <p className="text-sm text-slate-500 mb-2">Description</p>
                    <p className="text-slate-300 leading-relaxed mb-4">
                      {project.description || "No description available."}
                    </p>

                    {project.registry_url && (
                      <a
                        href={project.registry_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 text-green-400 hover:text-green-300 transition"
                      >
                        <ExternalLink className="w-4 h-4" />
                        <span>View on Registry</span>
                      </a>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* SECTION 2: AI-Generated Report */}
            <div
              className="bg-gradient-to-br from-slate-900/95 via-slate-800/95 to-slate-900/95 backdrop-blur-xl rounded-2xl shadow-2xl p-8 mb-8 border border-green-500/30 animate-slideIn"
              style={{ animationDelay: "0.1s" }}
            >
              <h2 className="text-2xl font-bold text-green-400 mb-6 flex items-center gap-2">
                <FileText className="w-6 h-6" />
                Comprehensive Project Report
              </h2>
              {reportLoading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500 mx-auto mb-4"></div>
                    <p className="text-slate-400 mb-4">Generating AI report...</p>
                    {currentProgress && (
                      <div className="mt-6">
                        <p className="text-green-400 font-medium mb-3">{currentProgress}</p>
                        <div className="space-y-2 max-w-md mx-auto">
                          {progressSteps.map((step, idx) => (
                            <div key={idx} className="flex items-center gap-3 text-sm">
                              <div className="w-2 h-2 bg-green-500 rounded-full flex-shrink-0"></div>
                              <span className="text-slate-300 text-left">{step.message}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ) : projectReport ? (
                <div className="prose prose-invert prose-green max-w-none">
                  <div 
                    className="text-slate-300 leading-relaxed"
                    dangerouslySetInnerHTML={{ __html: projectReport.report || "No report available." }}
                  />
                </div>
              ) : (
                <p className="text-slate-400 text-center py-8">
                  Report not available
                </p>
              )}
            </div>
          </>
        )}

        {/* SECTION 3/4: Ask Me Anything - Chat Interface (Common for both) */}
        <div
          className="bg-gradient-to-br from-slate-900/95 via-slate-800/95 to-slate-900/95 backdrop-blur-xl rounded-2xl shadow-2xl p-8 border border-blue-500/30 animate-slideIn"
          style={{ animationDelay: company ? "0.3s" : "0.2s" }}
        >
          <h2 className="text-2xl font-bold text-blue-400 mb-6 flex items-center gap-2">
            <MessageCircle className="w-6 h-6" />
            Ask Me Anything
          </h2>

          {/* Chat Messages */}
          <div className="mb-6 space-y-4 max-h-96 overflow-y-auto">
            {chatMessages.length === 0 ? (
              <div className="text-center py-8">
                <Sparkles className="w-12 h-12 text-blue-400 mx-auto mb-3 opacity-50" />
                <p className="text-slate-400">
                  Ask any question about {company ? "this company" : "this project"}
                </p>
              </div>
            ) : (
              chatMessages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex ${
                    msg.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`max-w-[80%] p-4 rounded-lg ${
                      msg.role === "user"
                        ? "bg-blue-600 text-white"
                        : "bg-slate-800 text-slate-200"
                    }`}
                  >
                    {msg.role === "assistant" ? (
                      <div 
                        className="prose prose-sm prose-invert max-w-none prose-headings:text-blue-300 prose-strong:text-blue-200 prose-a:text-blue-300"
                        dangerouslySetInnerHTML={{ __html: msg.content }}
                      />
                    ) : (
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    )}
                  </div>
                </div>
              ))
            )}
            {chatLoading && (
              <div className="flex justify-start">
                <div className="bg-slate-800 p-4 rounded-lg">
                  <div className="flex space-x-2">
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                    <div
                      className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0.1s" }}
                    ></div>
                    <div
                      className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0.2s" }}
                    ></div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Chat Input */}
          <div className="flex gap-3">
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={`Ask about ${company ? company.name : project?.name}...`}
              className="flex-1 px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={chatLoading}
            />
            <button
              onClick={handleSendMessage}
              disabled={chatLoading || !chatInput.trim()}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg transition flex items-center gap-2"
            >
              <Send className="w-5 h-5" />
              <span>Send</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportPage;
