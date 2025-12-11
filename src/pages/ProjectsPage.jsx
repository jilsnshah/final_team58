import React from "react";
import {
  ExternalLink,
  MapPin,
  Search,
  Sparkles,
  TrendingUp,
  Award,
} from "lucide-react";
import { Link } from "react-router-dom";
import api from "../services/api";

const ProjectsPage = () => {
  const [searchQuery, setSearchQuery] = React.useState("");
  const [isSearching, setIsSearching] = React.useState(false);
  const [suggestions, setSuggestions] = React.useState([]);
  const [showSuggestions, setShowSuggestions] = React.useState(false);
  const [selectedCategory, setSelectedCategory] = React.useState("All");
  const [projects, setProjects] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  const [displayedCount, setDisplayedCount] = React.useState(100); // Show 100 initially

  // Fetch projects from backend on mount
  React.useEffect(() => {
    const fetchProjects = async () => {
      try {
        setLoading(true);
        const response = await api.getProjects(5000); // Fetch all projects
        // API returns {count, data} structure
        const projectsData = Array.isArray(response)
          ? response
          : response?.data || [];
        setProjects(projectsData);
        setError(null);
      } catch (err) {
        console.error("Error fetching projects:", err);
        setError(
          "Failed to load projects. Please check if backend is running."
        );
        setProjects([]);
      } finally {
        setLoading(false);
      }
    };

    fetchProjects();

    // Optional: Set up WebSocket for real-time updates
    try {
      api.initWebSocket();
      api.onDataUpdate("projects", (data) => {
        const projectsData = Array.isArray(data) ? data : data?.data || [];
        setProjects(projectsData);
      });
    } catch (err) {
      console.warn("WebSocket not available:", err);
    }
  }, []);

  // Real semantic search using backend API
  const performSemanticSearch = async (query) => {
    if (!query.trim()) {
      setSuggestions([]);
      return;
    }

    setIsSearching(true);

    try {
      // Use backend search API
      const result = await api.searchProjects(query, 5);
      const projectResults = result.data || [];
      setSuggestions(projectResults);
    } catch (error) {
      console.error("Search error:", error);
      // Fallback to client-side filtering
      const searchTerms = query.toLowerCase().split(" ");
      const scored = projects.map((project) => {
        let score = 0;
        const searchableText =
          `${project.name} ${project.description} ${project.category} ${project.country} ${project.methodology}`.toLowerCase();

        searchTerms.forEach((term) => {
          if (searchableText.includes(term)) {
            score += 1;
            if (project.name?.toLowerCase().includes(term)) score += 2;
            if (project.category?.toLowerCase().includes(term)) score += 1.5;
          }
        });

        return { ...project, score };
      });

      const filtered = scored
        .filter((p) => p.score > 0)
        .sort((a, b) => b.score - a.score)
        .slice(0, 5);

      setSuggestions(filtered);
    } finally {
      setIsSearching(false);
    }
  };

  React.useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (searchQuery) {
        performSemanticSearch(searchQuery);
      }
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchQuery, projects]);

  const categories = [
    "All",
    ...new Set(
      (Array.isArray(projects) ? projects : []).map((p) => p.category)
    ),
  ];

  const filteredProjects =
    selectedCategory === "All"
      ? projects
      : (Array.isArray(projects) ? projects : []).filter(
          (p) => p.category === selectedCategory
        );

  // Only show limited number of projects
  const displayedProjects = Array.isArray(filteredProjects) 
    ? filteredProjects.slice(0, displayedCount) 
    : [];
  
  const hasMore = Array.isArray(filteredProjects) && filteredProjects.length > displayedCount;

  const loadMore = () => {
    setDisplayedCount(prev => prev + 100);
  };

  // Reset displayed count when category changes
  React.useEffect(() => {
    setDisplayedCount(100);
  }, [selectedCategory]);

  const getCategoryColor = (category) => {
    const colors = {
      Forestry: "bg-green-500/20 text-green-300 border-green-500/30",
      "Renewable Energy": "bg-blue-500/20 text-green-300 border-blue-500/30",
      "Blue Carbon": "bg-green-500/20 text-green-300 border-green-500/30",
      "Community Projects":
        "bg-purple-500/20 text-purple-300 border-purple-500/30",
      "Grassland Conservation":
        "bg-yellow-500/20 text-yellow-300 border-yellow-500/30",
    };
    return (
      colors[category] || "bg-slate-500/20 text-slate-300 border-slate-500/30"
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 relative overflow-hidden">
      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-green-500 mx-auto mb-4"></div>
            <p className="text-slate-400">Loading projects...</p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <div className="flex items-center justify-center min-h-screen p-4">
          <div className="max-w-md p-6 rounded-lg bg-slate-800 text-white">
            <h2 className="text-xl font-bold mb-2 text-red-500">
              Error Loading Projects
            </h2>
            <p className="text-slate-300">{error}</p>
            <p className="mt-4 text-sm text-slate-400">
              Make sure the backend server is running on port 5000.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="mt-4 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {/* Main Content */}
      {!loading && !error && (
        <>
          {/* Animated background elements */}
          <div className="absolute inset-0 overflow-hidden pointer-events-none">
            <div className="absolute top-20 left-20 w-96 h-96 bg-green-500/10 rounded-full blur-3xl animate-float"></div>
            <div
              className="absolute bottom-20 right-20 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-float"
              style={{ animationDelay: "1s" }}
            ></div>
          </div>

          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 relative z-10">
            {/* Header */}
            <div className="mb-8 animate-slideIn">
              <h1 className="text-4xl font-bold bg-gradient-to-r from-green-400 via-emerald-300 to-green-400 bg-clip-text text-transparent mb-3">
                Carbon Credit Projects
              </h1>
              <p className="text-slate-400 text-lg">
                Browse verified carbon offset projects from around the world.
                Support sustainable development while reducing your carbon
                footprint.
              </p>
            </div>

            {/* Semantic Search Bar */}
            <div
              className="mb-8 animate-slideIn relative z-50"
              style={{ animationDelay: "0.1s" }}
            >
              <div className="bg-gradient-to-br from-slate-900/95 via-slate-800/95 to-slate-900/95 backdrop-blur-xl rounded-2xl shadow-2xl p-6 border border-green-500/30">
                <div className="flex items-center gap-3 mb-4">
                  <Sparkles className="w-5 h-5 text-green-400 animate-pulse" />
                  <h2 className="text-xl font-bold text-green-400">
                    Find Your Perfect Carbon Project
                  </h2>
                </div>

                <div className="relative z-50">
                  <div className="relative">
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => {
                        setSearchQuery(e.target.value);
                        setShowSuggestions(true);
                      }}
                      onFocus={() => setShowSuggestions(true)}
                      onBlur={() =>
                        setTimeout(() => setShowSuggestions(false), 200)
                      }
                      placeholder="Search by project type, location, methodology, or keywords..."
                      className="w-full px-6 py-3 pl-12 pr-12 text-slate-200 bg-slate-800/50 backdrop-blur-xl border border-green-500/30 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-400 placeholder-slate-500 shadow-lg transition-all"
                    />
                    <Search className="absolute left-4 top-3.5 w-5 h-5 text-green-400" />
                    {isSearching && (
                      <Sparkles className="absolute right-4 top-3.5 w-5 h-5 text-green-400 animate-spin" />
                    )}
                  </div>

                  {/* Semantic Search Suggestions */}
                  {showSuggestions && suggestions.length > 0 && (
                    <div className="absolute top-full mt-2 w-full bg-slate-900 backdrop-blur-xl border border-slate-600 rounded-lg shadow-[0_20px_60px_-15px_rgba(0,0,0,0.8)] overflow-hidden animate-slideIn z-[9999]">
                      <div className="max-h-80 overflow-y-auto scrollbar-thin scrollbar-thumb-green-500/50 scrollbar-track-slate-800/50">
                        {suggestions.map((project) => (
                          <Link
                            key={project.id}
                            to={`/report/${project.id}`}
                            className="block px-4 py-3 hover:bg-slate-800 transition-all border-b border-slate-700/50 last:border-b-0 group"
                          >
                            <div className="flex items-start gap-3">
                              <img
                                src={project.image_url}
                                alt={project.name}
                                className="w-16 h-16 object-cover rounded-lg border border-green-500/20"
                              />
                              <div className="flex-1 min-w-0">
                                <div className="flex items-start justify-between gap-2">
                                  <h3 className="font-semibold text-slate-100 group-hover:text-green-400 transition line-clamp-1">
                                    {project.name}
                                  </h3>
                                  <span className="text-xs px-2 py-0.5 bg-green-500/20 text-green-300 rounded border border-green-500/30 whitespace-nowrap">
                                    {project.id}
                                  </span>
                                </div>
                                <div className="flex items-center gap-2 mt-1">
                                  <span
                                    className={`text-xs px-2 py-0.5 rounded border ${getCategoryColor(
                                      project.category
                                    )}`}
                                  >
                                    {project.category}
                                  </span>
                                  <span className="flex items-center gap-1 text-xs text-slate-300">
                                    <MapPin className="w-3 h-3" />
                                    {project.country}
                                  </span>
                                </div>
                                <p className="text-xs text-slate-400 mt-1 line-clamp-1">
                                  {project.description}
                                </p>
                                <div className="flex items-center gap-3 mt-2">
                                  <span className="text-sm font-bold text-green-400">
                                    ${project.price}/credit
                                  </span>
                                  <span className="text-xs text-slate-500">
                                    {project.available_credits.toLocaleString()}{" "}
                                    available
                                  </span>
                                </div>
                              </div>
                            </div>
                          </Link>
                        ))}
                      </div>
                      <div className="p-3 bg-slate-900/50 border-t border-green-500/20 text-center">
                        <p className="text-xs text-slate-500">
                          Click on a project to view detailed report and
                          registry information
                        </p>
                      </div>
                    </div>
                  )}
                </div>

                <p className="text-slate-500 text-xs mt-3">
                  Powered by semantic search - searches across project
                  descriptions, locations, and methodologies
                </p>
              </div>
            </div>

            {/* Category Filter */}
            <div
              className="mb-6 flex flex-wrap gap-3 animate-slideIn"
              style={{ animationDelay: "0.2s" }}
            >
              {categories.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`px-4 py-2 rounded-lg font-medium transition-all ${
                    selectedCategory === cat
                      ? "bg-gradient-to-r from-green-600 to-emerald-600 text-white shadow-lg shadow-green-500/30"
                      : "bg-slate-800/50 text-slate-400 border border-slate-700/50 hover:border-green-500/30 hover:text-green-400"
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>

            {/* Projects Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {displayedProjects.map((project, idx) => (
                  <div
                    key={project.id}
                    className="bg-gradient-to-br from-slate-900/95 via-slate-800/95 to-slate-900/95 backdrop-blur-xl rounded-2xl shadow-2xl hover:shadow-green-500/20 transition-all overflow-hidden border border-green-500/20 hover:border-green-400/50 group animate-slideIn"
                    style={{ animationDelay: `${0.3 + idx * 0.05}s` }}
                  >
                    <div className="relative overflow-hidden">
                      <img
                        src={project.image_url}
                        alt={project.name}
                        className="w-full h-48 object-cover group-hover:scale-110 transition-transform duration-500"
                      />
                      <div className="absolute top-3 right-3 bg-slate-900/90 backdrop-blur-sm px-2 py-1 rounded-lg border border-green-500/30">
                        <span className="text-xs text-slate-300 font-mono">
                          {project.id}
                        </span>
                      </div>
                    </div>

                    <div className="p-6">
                      <div className="flex items-start justify-between mb-3">
                        <span
                          className={`text-xs px-3 py-1 rounded-lg font-semibold border ${getCategoryColor(
                            project.category
                          )}`}
                        >
                          {project.category}
                        </span>
                        <span className="text-xs px-2 py-1 bg-slate-700/50 text-slate-400 rounded">
                          {project.vintage}
                        </span>
                      </div>

                      <h3 className="text-lg font-bold text-slate-200 group-hover:text-green-400 transition mb-2 line-clamp-2">
                        {project.name}
                      </h3>

                      <p className="text-sm text-slate-400 mb-4 line-clamp-3">
                        {project.description}
                      </p>

                      <div className="space-y-2 mb-4">
                        <div className="flex items-center text-sm text-slate-300">
                          <MapPin className="w-4 h-4 mr-2 text-green-400" />
                          <span>{project.country}</span>
                        </div>
                        <div className="flex items-center text-sm text-slate-300">
                          <Award className="w-4 h-4 mr-2 text-green-400" />
                          <span className="font-semibold">
                            {project.methodology}
                          </span>
                        </div>
                      </div>

                      <div className="bg-slate-800/50 border border-green-500/20 p-4 rounded-xl mb-4">
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-sm text-slate-400">
                            Price per Credit
                          </span>
                          <span className="text-2xl font-bold text-green-400">
                            ${project.price}
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-slate-400">
                            Available
                          </span>
                          <span className="text-sm font-semibold text-slate-200">
                            {project.available_credits.toLocaleString()} credits
                          </span>
                        </div>
                      </div>

                      <Link
                        to={`/report/${project.id}`}
                        className="w-full bg-gradient-to-r from-green-600 to-emerald-600 text-white py-2.5 rounded-lg font-semibold hover:shadow-lg hover:shadow-green-500/50 transition-all flex items-center justify-center space-x-2"
                      >
                        <TrendingUp className="w-4 h-4" />
                        <span>View Project Report</span>
                      </Link>
                    </div>
                  </div>
                ))}
            </div>

            {/* Load More Button */}
            {hasMore && (
              <div className="mt-8 flex justify-center animate-slideIn">
                <button
                  onClick={loadMore}
                  className="group relative px-8 py-3 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-xl font-semibold hover:shadow-lg hover:shadow-green-500/50 transition-all flex items-center space-x-2"
                >
                  <span>Load More Projects</span>
                  <TrendingUp className="w-5 h-5 group-hover:translate-y-1 transition-transform" />
                </button>
              </div>
            )}

            {/* Showing count indicator */}
            <div className="mt-6 text-center text-slate-400 text-sm">
              Showing {displayedProjects.length} of {filteredProjects.length} projects
              {selectedCategory !== "All" && ` in ${selectedCategory}`}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default ProjectsPage;
