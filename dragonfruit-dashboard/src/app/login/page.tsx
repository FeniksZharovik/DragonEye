'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faDragon, faEye, faEyeSlash } from '@fortawesome/free-solid-svg-icons';
import { fetchFromAPI } from '@/lib/api';

export default function Login() {
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      // Use your API helper
      const data = await fetchFromAPI<{ 
        session_id: string;
        user: { uid: string; username: string; email: string } 
      }>(
        '/api/auth/login',
        {
          method: 'POST',
          credentials: 'include',
          body: JSON.stringify({
            username_or_email: formData.email,
            password: formData.password
          }),
        }
      );

      // Store session_id in localStorage as backup
      if (data.session_id) {
        localStorage.setItem('session_id', data.session_id);
        console.log('✅ Session ID stored in localStorage');
      }

      // Success: redirect to dashboard
      router.push('/dashboard');
    } catch (err: any) {
      console.error('Login error:', err);
      // Parse error from your FastAPI response
      if (err.message.includes('401')) {
        setError('Invalid email or password');
      } else if (err.message.includes('400') || err.message.includes('422')) {
        setError('Please check your input');
      } else {
        setError('Login failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  return (
    <div className="min-h-screen flex">
      {/* Left side - Form */}
      <div className="w-full lg:w-1/2 p-8 lg:p-16 flex flex-col justify-center bg-white">
        <div className="max-w-md mx-auto w-full">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Sign In</h1>
          <p className="text-gray-500 mb-8">Enter your email and password to sign in!</p>

          {error && (
            <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-lg text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            {/* Email field */}
            <div className="mb-6 text-black">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email<span className="text-red-500">*</span>
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="info@gmail.com"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
                required
              />
            </div>

            {/* Password field */}
            <div className="mb-6 text-black">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Password<span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="Enter your password"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                >
                  {showPassword ? (
                      <FontAwesomeIcon 
                        icon={faEye} 
                        className="text-gray-800" 
                        fontSize={15} 
                      />
                  ) : (
                  
                    <FontAwesomeIcon 
                      icon={faEyeSlash} 
                      className="text-gray-800"
                      fontSize={15} 
                    />
                  )}
                </button>
              </div>
            </div>

            {/* Remember me and forgot password */}
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center">
                <input
                  id="remember-me"
                  type="checkbox"
                  className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                />
                <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-700">
                  Keep me logged in
                </label>
              </div>
              <a href="#" className="text-sm text-blue-600 hover:text-blue-800 font-medium">
                Forgot password?
              </a>
            </div>

            {/* Sign in button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-70"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <p className="mt-6 text-sm text-gray-600 text-center">
            Don't have an account?{' '}
            <a href="#" className="text-blue-600 hover:text-blue-800 font-medium">
              Sign Up
            </a>
          </p>
        </div>
      </div>

      {/* Right side - Branding */}
      <div className="hidden lg:block w-1/2 bg-pink-900 relative overflow-hidden">
        <div className="absolute inset-0 opacity-20">
          <div className="grid grid-cols-12 gap-4 h-full">
            {Array.from({ length: 48 }).map((_, i) => (
              <div key={i} className="bg-pink-500 rounded-sm"></div>
            ))}
          </div>
        </div>

        <div className="absolute inset-0 flex flex-col items-center justify-center p-16 text-white">
          <div className="flex items-center mb-6">
            <div className="w-12 h-12 bg-red-500 rounded-lg flex items-center justify-center mr-4">
              <FontAwesomeIcon 
                icon={faDragon} 
                className="text-[30px] text-gray-800" 
              />
            </div>
            <h2 className="text-4xl font-bold">DragonFruit</h2>
          </div>
          <p className="text-xl text-center max-w-md">
            Sistem Grading Buah Naga Super Merah (Hylocereus Costaricensis) Berbasis Pengolahan Citra Digital dan Fuzzy Logic Terintegrasi dengan Embedded System
          </p>
        </div>
      </div>
    </div>
  );
}