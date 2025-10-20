// import React from 'react';
// import { Link, useNavigate } from 'react-router-dom';
// import { useAuth } from '../contexts/AuthContext';

// export const HomePage: React.FC = () => {
//   const { isAuthenticated } = useAuth();
//   const navigate = useNavigate();

//   const handleGetStarted = () => {
//     if (isAuthenticated) {
//       navigate('/dashboard');
//     } else {
//       navigate('/signup');
//     }
//   };

//   return (
//     <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
//       {/* Navigation */}
//       <nav className="px-6 py-4 flex justify-between items-center border-b border-gray-800">
//         <div className="flex items-center space-x-2">
//           <h1 className="text-2xl font-bold text-white">InvestIQ</h1>
//         </div>
//         <div className="flex items-center space-x-4">
//           {isAuthenticated ? (
//             <Link
//               to="/dashboard"
//               className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
//             >
//               Go to Dashboard
//             </Link>
//           ) : (
//             <>
//               <Link
//                 to="/login"
//                 className="px-4 py-2 text-gray-300 hover:text-white transition-colors"
//               >
//                 Sign In
//               </Link>
//               <Link
//                 to="/signup"
//                 className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
//               >
//                 Sign Up
//               </Link>
//             </>
//           )}
//         </div>
//       </nav>

//       {/* Hero Section */}
//       <div className="max-w-7xl mx-auto px-6 py-20">
//         <div className="text-center space-y-8">
//           {/* Main Heading */}
//           <div className="space-y-4">
//             <h1 className="text-5xl md:text-6xl font-bold text-white">
//               AI-Powered
//               <span className="bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
//                 {' '}Financial Analysis
//               </span>
//             </h1>
//             <p className="text-xl text-gray-400 max-w-3xl mx-auto">
//               Get instant insights on stocks with natural language queries. Powered by advanced AI and real-time market data.
//             </p>
//           </div>

//           {/* CTA Buttons */}
//           <div className="flex justify-center space-x-4">
//             <button
//               onClick={handleGetStarted}
//               className="px-8 py-4 bg-blue-600 hover:bg-blue-700 text-white text-lg font-semibold rounded-lg transition-colors shadow-lg"
//             >
//               Get Started Free
//             </button>
//             <Link
//               to="/login"
//               className="px-8 py-4 bg-gray-800 hover:bg-gray-700 text-white text-lg font-semibold rounded-lg border border-gray-700 transition-colors"
//             >
//               Watch Demo
//             </Link>
//           </div>

//           {/* Features Grid */}
//           <div className="grid md:grid-cols-3 gap-8 mt-20">
//             <div className="bg-gray-800 p-8 rounded-xl border border-gray-700">
//               <div className="text-blue-400 text-4xl mb-4">🤖</div>
//               <h3 className="text-xl font-semibold text-white mb-2">
//                 AI-Powered Analysis
//               </h3>
//               <p className="text-gray-400">
//                 Ask questions in natural language and get comprehensive financial analysis
//               </p>
//             </div>

//             <div className="bg-gray-800 p-8 rounded-xl border border-gray-700">
//               <div className="text-green-400 text-4xl mb-4">📊</div>
//               <h3 className="text-xl font-semibold text-white mb-2">
//                 Real-Time Data
//               </h3>
//               <p className="text-gray-400">
//                 Access live stock prices, financial statements, and market metrics
//               </p>
//             </div>

//             <div className="bg-gray-800 p-8 rounded-xl border border-gray-700">
//               <div className="text-purple-400 text-4xl mb-4">💬</div>
//               <h3 className="text-xl font-semibold text-white mb-2">
//                 Conversation Context
//               </h3>
//               <p className="text-gray-400">
//                 Follow-up questions with memory of previous queries in the conversation
//               </p>
//             </div>
//           </div>

//           {/* Example Queries */}
//           <div className="mt-20">
//             <h2 className="text-3xl font-bold text-white mb-8">
//               Try asking questions like:
//             </h2>
//             <div className="grid md:grid-cols-2 gap-4 max-w-4xl mx-auto">
//               <div className="bg-gray-800 p-4 rounded-lg border border-gray-700 text-left">
//                 <p className="text-gray-300">
//                   💡 "How is Apple stock performing?"
//                 </p>
//               </div>
//               <div className="bg-gray-800 p-4 rounded-lg border border-gray-700 text-left">
//                 <p className="text-gray-300">
//                   💡 "Compare Tesla and Amazon stocks"
//                 </p>
//               </div>
//               <div className="bg-gray-800 p-4 rounded-lg border border-gray-700 text-left">
//                 <p className="text-gray-300">
//                   💡 "What are Microsoft's key financial metrics?"
//                 </p>
//               </div>
//               <div className="bg-gray-800 p-4 rounded-lg border border-gray-700 text-left">
//                 <p className="text-gray-300">
//                   💡 "Is Netflix stock overvalued?"
//                 </p>
//               </div>
//             </div>
//           </div>
//         </div>
//       </div>

//       {/* Footer */}
//       <footer className="border-t border-gray-800 mt-20 py-8">
//         <div className="max-w-7xl mx-auto px-6 text-center text-gray-500">
//           <p>© 2025 InvestIQ. All rights reserved.</p>
//         </div>
//       </footer>
//     </div>
//   );
// };


// // import { Link } from 'react-router-dom';
// // import { ArrowRight } from "lucide-react"
// // import { useEffect, useState } from "react"

// // export default function HomePage() {


// //   const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 })
// //   const [currentFeature, setCurrentFeature] = useState(0)

// //   const features = [
// //     "Real-time stock analysis and financial metrics",
// //     "Natural language queries with contextual memory",
// //     "Autonomous market monitoring and insights",
// //   ]

// //   useEffect(() => {
// //     const handleMouseMove = (e: MouseEvent) => {
// //       setMousePosition({ x: e.clientX, y: e.clientY })
// //     }

// //     window.addEventListener("mousemove", handleMouseMove)
// //     return () => window.removeEventListener("mousemove", handleMouseMove)
// //   }, [])

// //   useEffect(() => {
// //     const interval = setInterval(() => {
// //       setCurrentFeature((prev) => (prev + 1) % features.length)
// //     }, 2000)
// //     return () => clearInterval(interval)
// //   }, [features.length])

// //   return (
// //     <div className="min-h-screen bg-black text-white flex flex-col overflow-hidden relative">
// //       <div className="fixed inset-0 pointer-events-none">
// //         <div
// //           className="absolute w-96 h-96 bg-purple-600/20 rounded-full blur-3xl opacity-0 animate-pulse"
// //           style={{
// //             left: `${mousePosition.x - 192}px`,
// //             top: `${mousePosition.y - 192}px`,
// //             transition: "all 0.3s ease-out",
// //           }}
// //         />
// //         <div
// //           className="absolute top-0 right-0 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl animate-pulse"
// //           style={{ animationDelay: "1s" }}
// //         />
// //         <div
// //           className="absolute bottom-0 left-1/4 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl animate-pulse"
// //           style={{ animationDelay: "2s" }}
// //         />
// //       </div>

// //       {/* Navigation */}
// //       <nav className="border-b border-white/10 px-8 py-4 flex justify-between items-center relative z-10 backdrop-blur-sm">
// //         <div className="text-xl font-bold tracking-tight bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
// //           InvestIQ
// //         </div>
// //         <div className="flex items-center gap-4">
      
// //           <Link to="/signin" className="text-sm text-white/60 hover:text-white transition-colors duration-300">
// //             Sign In
// //           </Link>
// //           <Link
// //             to="/signup"
// //             className="px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white text-sm rounded-lg transition-all duration-300 shadow-lg hover:shadow-purple-500/50"
// //           >
// //             Sign Up
// //           </Link>
// //         </div>
// //       </nav>

// //       {/* Main Content */}
// //       <div className="flex-1 flex items-center justify-center px-8 relative z-10">
// //         <div className="max-w-3xl w-full space-y-12 text-center">
// //           <div className="space-y-6 animate-fade-in">
// //             <div className="inline-block">
// //               <span className="text-xs font-semibold text-purple-400 tracking-widest uppercase">
// //                 Autonomous Intelligence
// //               </span>
// //             </div>
// //             <h1 className="text-6xl md:text-7xl font-bold tracking-tight leading-tight">
// //               <span className="bg-gradient-to-r from-white via-purple-200 to-blue-200 bg-clip-text text-transparent">
// //                 Financial Intelligence Agent
// //               </span>
// //             </h1>
// //             <p className="text-lg text-white/50 max-w-2xl mx-auto leading-relaxed">
// //               Autonomous AI agent for real-time financial analysis and market insights. Monitor, analyze, and act on
// //               market opportunities 24/7.
// //             </p>
// //           </div>

// //           <div className="flex justify-center pt-4">
// //             <Link
// //               to="/dashboard"
// //               className="group inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white rounded-lg transition-all duration-300 shadow-xl hover:shadow-purple-500/50 hover:scale-105"
// //             >
// //               Start Agent
// //               <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
// //             </Link>
// //           </div>

// //           <div className="pt-16 space-y-4 text-left max-w-xl mx-auto">
// //             <div className="relative h-24 flex items-center overflow-hidden">
// //               <div className="absolute inset-0 flex items-center">
// //                 {features.map((feature, index) => (
// //                   <div
// //                     key={index}
// //                     className={`absolute inset-0 flex items-center transition-all duration-500 ease-in-out ${
// //                       index === currentFeature
// //                         ? "opacity-100 translate-x-0"
// //                         : index < currentFeature
// //                           ? "opacity-0 -translate-x-full"
// //                           : "opacity-0 translate-x-full"
// //                     }`}
// //                   >
// //                     <div className="group flex items-start gap-4 p-4 rounded-lg hover:bg-white/5 transition-all duration-300 cursor-default w-full">
// //                       <div className="w-1.5 h-1.5 bg-gradient-to-r from-purple-400 to-blue-400 rounded-full mt-2 flex-shrink-0 group-hover:scale-150 transition-transform" />
// //                       <p className="text-sm text-white/70 group-hover:text-white/90 transition-colors">{feature}</p>
// //                     </div>
// //                   </div>
// //                 ))}
// //               </div>
// //             </div>
// //           </div>
// //         </div>
// //       </div>

// //       <footer className="border-t border-white/10 px-8 py-6 text-center text-sm text-white/40 relative z-10 backdrop-blur-sm">
// //         <p>© 2025 InvestIQ. Financial Intelligence Agent.</p>
// //       </footer>
// //     </div>
// //   )
// // }


import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";

export const HomePage: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const handleGetStarted = () => {
    if (isAuthenticated) {
      navigate("/dashboard");
    } else {
      navigate("/signup");
    }
  };

  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [currentFeature, setCurrentFeature] = useState(0);

  const features = [
    "Real-time stock analysis and financial metrics",
    "Natural language queries with contextual memory",
    "Autonomous market monitoring and insights",
  ];

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({ x: e.clientX, y: e.clientY });
    };
    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentFeature((prev) => (prev + 1) % features.length);
    }, 2000);
    return () => clearInterval(interval);
  }, [features.length]);

  return (
    <div className="min-h-screen bg-black text-white flex flex-col overflow-hidden relative">
      {/* Background Effects */}
      <div className="fixed inset-0 pointer-events-none">
        <div
          className="absolute w-96 h-96 bg-purple-600/20 rounded-full blur-3xl opacity-0 animate-pulse"
          style={{
            left: `${mousePosition.x - 192}px`,
            top: `${mousePosition.y - 192}px`,
            transition: "all 0.3s ease-out",
          }}
        />
        <div
          className="absolute top-0 right-0 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl animate-pulse"
          style={{ animationDelay: "1s" }}
        />
        <div
          className="absolute bottom-0 left-1/4 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl animate-pulse"
          style={{ animationDelay: "2s" }}
        />
      </div>

      {/* Navigation */}
      <nav className="border-b border-white/10 px-8 py-4 flex justify-between items-center relative z-10 backdrop-blur-sm">
        <div className="text-xl font-bold tracking-tight bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
          InvestIQ
        </div>
        <div className="flex items-center gap-4">
          {isAuthenticated ? (
            <Link
              to="/dashboard"
              className="px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white text-sm rounded-lg transition-all duration-300 shadow-lg hover:shadow-purple-500/50"
            >
              Dashboard
            </Link>
          ) : (
            <>
              <Link
                to="/login"
                className="text-sm text-white/60 hover:text-white transition-colors duration-300"
              >
                Sign In
              </Link>
              <Link
                to="/signup"
                className="px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white text-sm rounded-lg transition-all duration-300 shadow-lg hover:shadow-purple-500/50"
              >
                Sign Up
              </Link>
            </>
          )}
        </div>
      </nav>

      {/* Main Section */}
      <div className="flex-1 flex items-center justify-center px-8 relative z-10">
        <div className="max-w-3xl w-full space-y-12 text-center">
          <div className="space-y-6 animate-fade-in">
            <div className="inline-block">
              <span className="text-xs font-semibold text-purple-400 tracking-widest uppercase">
                Autonomous Intelligence
              </span>
            </div>
            <h1 className="text-6xl md:text-7xl font-bold tracking-tight leading-tight">
              <span className="bg-gradient-to-r from-white via-purple-200 to-blue-200 bg-clip-text text-transparent">
                Financial Intelligence Agent
              </span>
            </h1>
            <p className="text-lg text-white/50 max-w-2xl mx-auto leading-relaxed">
              AI-powered agent for real-time financial analysis and autonomous
              market insights. Monitor, analyze, and act on opportunities 24/7.
            </p>
          </div>

          <div className="flex justify-center pt-4">
            <button
              onClick={handleGetStarted}
              className="group inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white rounded-lg transition-all duration-300 shadow-xl hover:shadow-purple-500/50 hover:scale-105"
            >
              Get Started
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>

          {/* Animated Features */}
          <div className="pt-16 space-y-4 text-left max-w-xl mx-auto">
            <div className="relative h-24 flex items-center overflow-hidden">
              <div className="absolute inset-0 flex items-center">
                {features.map((feature, index) => (
                  <div
                    key={index}
                    className={`absolute inset-0 flex items-center transition-all duration-500 ease-in-out ${
                      index === currentFeature
                        ? "opacity-100 translate-x-0"
                        : index < currentFeature
                        ? "opacity-0 -translate-x-full"
                        : "opacity-0 translate-x-full"
                    }`}
                  >
                    <div className="group flex items-start gap-4 p-4 rounded-lg hover:bg-white/5 transition-all duration-300 cursor-default w-full">
                      <div className="w-1.5 h-1.5 bg-gradient-to-r from-purple-400 to-blue-400 rounded-full mt-2 flex-shrink-0 group-hover:scale-150 transition-transform" />
                      <p className="text-sm text-white/70 group-hover:text-white/90 transition-colors">
                        {feature}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-white/10 px-8 py-6 text-center text-sm text-white/40 relative z-10 backdrop-blur-sm">
        <p>© 2025 InvestIQ. Financial Intelligence Agent.</p>
      </footer>
    </div>
  );
};
