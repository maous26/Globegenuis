import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Plane, Zap, Star, Users, Globe, 
  CheckCircle, ArrowRight, Bell, Euro, Percent, Clock
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { checkBackendHealth } from '../services/api';

const Landing = () => {
  const { user } = useAuth();
  const [scrollY, setScrollY] = useState(0);
  const [apiStatus, setApiStatus] = useState('checking');
  
  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', handleScroll);
    
    // Check backend health
    checkBackendHealth()
      .then(data => {
        console.log('Backend health check result:', data);
        setApiStatus('healthy');
      })
      .catch(error => {
        console.error('Backend health check failed:', error);
        setApiStatus('error');
      });
    
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className={`fixed w-full z-50 transition-all duration-300 ${
        scrollY > 50 ? 'bg-white shadow-lg' : 'bg-transparent'
      }`}>
        <nav className="container mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-2">
              <Plane className="h-8 w-8 text-blue-600" />
              <span className="text-2xl font-bold text-gray-900">GlobeGenius</span>
            </div>
            
            <div className="flex items-center space-x-6">
              <a href="#features" className="text-gray-700 hover:text-blue-600 font-medium hidden md:inline">
                Fonctionnalités
              </a>
              <a href="#pricing" className="text-gray-700 hover:text-blue-600 font-medium hidden md:inline">
                Tarifs
              </a>
              {user ? (
                <Link 
                  to="/dashboard" 
                  className="bg-blue-600 text-white px-6 py-2.5 rounded-full font-semibold 
                           hover:bg-blue-700 transition-all transform hover:scale-105"
                >
                  Dashboard
                </Link>
              ) : (
                <>
                  <Link 
                    to="/login" 
                    className="text-blue-600 hover:text-blue-800 font-semibold 
                             px-4 py-2 rounded-lg hover:bg-blue-50 transition-all"
                  >
                    Se connecter
                  </Link>
                  <Link 
                    to="/signup" 
                    className="bg-blue-600 text-white px-6 py-2.5 rounded-full font-semibold 
                             hover:bg-blue-700 transition-all transform hover:scale-105"
                  >
                    Essai gratuit
                  </Link>
                </>
              )}
            </div>
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 px-4 bg-gradient-to-br from-blue-50 via-white to-indigo-50 overflow-hidden">
        {/* Animated background elements */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-blue-200 rounded-full opacity-30 blur-3xl" />
          <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-indigo-200 rounded-full opacity-30 blur-3xl" />
        </div>

        <div className="container mx-auto relative z-10">
          <div className="max-w-5xl mx-auto text-center">
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="mb-6"
            >
              <span className="inline-block px-4 py-2 bg-blue-100 text-blue-700 rounded-full 
                             text-sm font-semibold mb-4">
                🚀 Plus de 50 000€ économisés par nos utilisateurs ce mois-ci
              </span>
            </motion.div>

            <motion.h1 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="text-5xl md:text-7xl font-bold text-gray-900 mb-6 leading-tight"
            >
              Économisez jusqu'à
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600"> 80%</span>
              <br />sur vos billets d'avion
            </motion.h1>
            
            <motion.p 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto"
            >
              Notre IA analyse en temps réel des millions de tarifs pour détecter 
              les <strong>prix cassés</strong>, <strong>erreurs tarifaires</strong> et 
              <strong>promotions flash</strong> avant qu'elles ne disparaissent.
            </motion.p>
            
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="flex flex-col sm:flex-row justify-center items-center space-y-4 sm:space-y-0 sm:space-x-4"
            >
              <Link 
                to="/signup" 
                className="group relative px-8 py-4 bg-blue-600 text-white rounded-full 
                         font-bold text-lg shadow-xl hover:shadow-2xl transform hover:scale-105 
                         transition-all duration-200 flex items-center"
              >
                Commencer gratuitement
                <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Link>
              
              <Link 
                to="/login"
                className="px-8 py-4 bg-white text-blue-600 border-2 border-blue-600 
                         rounded-full font-semibold hover:bg-blue-50 transition-all 
                         flex items-center"
              >
                Déjà client ? Se connecter
              </Link>
            </motion.div>

            {/* Demo button moved below */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="mt-4"
            >
              <button 
                onClick={() => {
                  const demoSection = document.getElementById('how-it-works');
                  demoSection?.scrollIntoView({ behavior: 'smooth' });
                }}
                className="text-gray-600 hover:text-blue-600 font-medium underline 
                         decoration-dotted underline-offset-4 transition-colors"
              >
                Voir une démo →
              </button>
            </motion.div>

            {/* Social proof */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 1, delay: 0.6 }}
              className="mt-12 flex flex-col sm:flex-row items-center justify-center space-y-4 sm:space-y-0 sm:space-x-8"
            >
              <div className="flex items-center">
                <div className="flex -space-x-2">
                  {[...Array(4)].map((_, i) => (
                    <img 
                      key={i} 
                      className="w-10 h-10 rounded-full border-2 border-white"
                      src={`https://i.pravatar.cc/40?img=${i + 1}`}
                      alt={`User ${i + 1}`}
                    />
                  ))}
                </div>
                <span className="ml-3 text-gray-600 font-medium">
                  +10 000 voyageurs actifs
                </span>
              </div>
              
              <div className="flex items-center space-x-1">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-5 h-5 fill-yellow-400 text-yellow-400" />
                ))}
                <span className="ml-2 text-gray-600 font-medium">4.9/5 (2,847 avis)</span>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {[
              { icon: Euro, value: '427€', label: 'Économie moyenne par vol' },
              { icon: Percent, value: '93%', label: 'Taux de satisfaction' },
              { icon: Clock, value: '24/7', label: 'Surveillance en temps réel' },
              { icon: Users, value: '50K+', label: 'Utilisateurs actifs' },
            ].map((stat, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="text-center"
              >
                <stat.icon className="w-12 h-12 text-blue-600 mx-auto mb-4" />
                <div className="text-3xl md:text-4xl font-bold text-gray-900 mb-2">{stat.value}</div>
                <div className="text-sm md:text-base text-gray-600">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="py-20 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Comment ça marche ?
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Notre technologie exclusive détecte automatiquement les meilleures opportunités
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {[
              {
                step: '1',
                title: 'Surveillance 24/7',
                description: 'Notre IA analyse en permanence des millions de tarifs sur toutes les compagnies aériennes',
                icon: Globe,
                color: 'bg-blue-100 text-blue-600'
              },
              {
                step: '2',
                title: 'Détection instantanée',
                description: 'Dès qu\'un prix chute anormalement, notre algorithme le détecte et vérifie sa validité',
                icon: Zap,
                color: 'bg-green-100 text-green-600'
              },
              {
                step: '3',
                title: 'Alerte immédiate',
                description: 'Vous recevez une notification avec le lien direct pour réserver avant que l\'offre ne disparaisse',
                icon: Bell,
                color: 'bg-purple-100 text-purple-600'
              }
            ].map((item, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="relative"
              >
                <div className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-shadow">
                  <div className={`w-16 h-16 ${item.color} rounded-2xl flex items-center justify-center mb-6`}>
                    <item.icon className="w-8 h-8" />
                  </div>
                  <div className="text-5xl font-bold text-gray-200 absolute top-4 right-4">{item.step}</div>
                  <h3 className="text-2xl font-bold text-gray-900 mb-4">{item.title}</h3>
                  <p className="text-gray-600">{item.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="py-20 bg-white">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Toutes les opportunités, aucune ne vous échappe
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Notre technologie détecte tous les types de bonnes affaires
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {[
              {
                title: 'Erreurs de prix',
                description: 'Les fameuses "error fares" où les compagnies se trompent dans leurs tarifs',
                example: 'Ex: Paris-New York à 89€ au lieu de 890€',
                icon: '🎯',
                badge: 'Jusqu\'à -90%'
              },
              {
                title: 'Ventes flash',
                description: 'Promotions limitées dans le temps des compagnies aériennes',
                example: 'Ex: 48h de promo Ryanair -50% toutes destinations',
                icon: '⚡',
                badge: '-30% à -70%'
              },
              {
                title: 'Prix cassés',
                description: 'Tarifs anormalement bas dus à la concurrence ou faible demande',
                example: 'Ex: Paris-Bangkok 380€ A/R en haute saison',
                icon: '💰',
                badge: '-40% à -60%'
              },
              {
                title: 'Promotions cachées',
                description: 'Offres non publicisées accessibles via des liens spécifiques',
                example: 'Ex: Code promo secret Lufthansa -25%',
                icon: '🔍',
                badge: '-20% à -40%'
              },
              {
                title: 'Tarifs négociés',
                description: 'Prix spéciaux normalement réservés aux agences',
                example: 'Ex: Tarif corporate Air France accessible',
                icon: '🤝',
                badge: '-15% à -35%'
              },
              {
                title: 'Combinaisons malignes',
                description: 'Itinéraires alternatifs moins chers que les vols directs',
                example: 'Ex: Paris-Miami via Madrid 40% moins cher',
                icon: '🧩',
                badge: '-25% à -45%'
              }
            ].map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="bg-gray-50 rounded-2xl p-6 hover:shadow-lg transition-all"
              >
                <div className="flex items-start justify-between mb-4">
                  <span className="text-4xl">{feature.icon}</span>
                  <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-semibold">
                    {feature.badge}
                  </span>
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-gray-600 mb-3">{feature.description}</p>
                <p className="text-sm text-blue-600 italic">{feature.example}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-20 bg-gradient-to-br from-blue-50 to-indigo-50">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Ils ont économisé des milliers d'euros
            </h2>
            <p className="text-xl text-gray-600">Découvrez leurs histoires</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {[
              {
                name: 'Marie L.',
                role: 'Entrepreneuse',
                savings: '3,200€',
                text: 'J\'ai économisé plus de 3000€ sur mes voyages d\'affaires cette année. L\'alerte pour Tokyo à -75% était incroyable !',
                trips: '12 voyages',
                avatar: 'https://i.pravatar.cc/100?img=1'
              },
              {
                name: 'Thomas D.',
                role: 'Digital Nomad',
                savings: '5,800€',
                text: 'GlobeGenius a transformé ma façon de voyager. Je peux maintenant me permettre 2x plus de destinations.',
                trips: '24 voyages',
                avatar: 'https://i.pravatar.cc/100?img=2'
              },
              {
                name: 'Sophie M.',
                role: 'Famille de 4',
                savings: '2,400€',
                text: 'Avec 2 enfants, les vacances coûtent cher. Grâce à GlobeGenius, on a pu partir aux Maldives pour le prix de l\'Espagne !',
                trips: '6 voyages',
                avatar: 'https://i.pravatar.cc/100?img=3'
              }
            ].map((testimonial, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="bg-white rounded-2xl p-8 shadow-lg"
              >
                <div className="flex items-center mb-4">
                  <img 
                    src={testimonial.avatar} 
                    alt={testimonial.name}
                    className="w-12 h-12 rounded-full mr-4"
                  />
                  <div>
                    <div className="font-bold text-gray-900">{testimonial.name}</div>
                    <div className="text-sm text-gray-600">{testimonial.role}</div>
                  </div>
                </div>
                <div className="flex text-yellow-400 mb-4">
                  {[...Array(5)].map((_, i) => (
                    <Star key={i} className="w-5 h-5 fill-current" />
                  ))}
                </div>
                <p className="text-gray-700 mb-4 italic">"{testimonial.text}"</p>
                <div className="flex justify-between text-sm">
                  <span className="text-green-600 font-bold">Économisé: {testimonial.savings}</span>
                  <span className="text-gray-500">{testimonial.trips}</span>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="py-20 bg-white">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Un abonnement rentabilisé dès le premier vol
            </h2>
            <p className="text-xl text-gray-600">Sans engagement, annulez à tout moment</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {/* Gratuit */}
            <div className="bg-gray-50 rounded-2xl p-8">
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Gratuit</h3>
              <div className="text-4xl font-bold text-gray-900 mb-6">0€</div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-center">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                  <span>3 alertes par mois</span>
                </li>
                <li className="flex items-center">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                  <span>Deals &gt; -50% uniquement</span>
                </li>
                <li className="flex items-center text-gray-400">
                  <CheckCircle className="w-5 h-5 mr-2 flex-shrink-0" />
                  <span>Alertes différées (2h)</span>
                </li>
              </ul>
              <Link to="/signup" className="block w-full text-center py-3 bg-gray-200 text-gray-800 rounded-lg font-semibold hover:bg-gray-300 transition-colors">
                Commencer
              </Link>
            </div>

            {/* Premium - Highlighted */}
            <div className="bg-blue-600 text-white rounded-2xl p-8 transform md:scale-105 shadow-2xl">
              <div className="flex justify-between items-center mb-2">
                <h3 className="text-2xl font-bold">Premium</h3>
                <span className="px-3 py-1 bg-yellow-400 text-gray-900 rounded-full text-sm font-bold">
                  Populaire
                </span>
              </div>
              <div className="text-4xl font-bold mb-6">9,99€<span className="text-lg font-normal">/mois</span></div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-center">
                  <CheckCircle className="w-5 h-5 text-white mr-2 flex-shrink-0" />
                  <span>Alertes illimitées</span>
                </li>
                <li className="flex items-center">
                  <CheckCircle className="w-5 h-5 text-white mr-2 flex-shrink-0" />
                  <span>Tous les deals (dès -20%)</span>
                </li>
                <li className="flex items-center">
                  <CheckCircle className="w-5 h-5 text-white mr-2 flex-shrink-0" />
                  <span>Alertes instantanées</span>
                </li>
                <li className="flex items-center">
                  <CheckCircle className="w-5 h-5 text-white mr-2 flex-shrink-0" />
                  <span>Support prioritaire</span>
                </li>
              </ul>
              <Link to="/signup" className="block w-full text-center py-3 bg-white text-blue-600 rounded-lg font-bold hover:bg-gray-100 transition-colors">
                Essai gratuit 7 jours
              </Link>
            </div>

            {/* Business */}
            <div className="bg-gray-50 rounded-2xl p-8">
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Business</h3>
              <div className="text-4xl font-bold text-gray-900 mb-6">29,99€<span className="text-lg font-normal">/mois</span></div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-center">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                  <span>Tout Premium +</span>
                </li>
                <li className="flex items-center">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                  <span>Multi-utilisateurs (5)</span>
                </li>
                <li className="flex items-center">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                  <span>API access</span>
                </li>
                <li className="flex items-center">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                  <span>Rapports mensuels</span>
                </li>
              </ul>
              <a href="mailto:contact@globegenius.com" className="block w-full text-center py-3 bg-gray-200 text-gray-800 rounded-lg font-semibold hover:bg-gray-300 transition-colors">
                Nous contacter
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-20 bg-gradient-to-r from-indigo-600 to-purple-600">
        <div className="container mx-auto px-4 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Prêt à économiser sur vos prochains voyages ?
            </h2>
            <p className="text-xl text-indigo-100 mb-10 max-w-2xl mx-auto">
              Rejoignez des milliers de voyageurs qui économisent déjà grâce à notre IA
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Link 
                to="/signup"
                className="bg-white text-indigo-600 px-8 py-4 rounded-lg font-bold text-lg hover:bg-gray-100 transition shadow-lg"
              >
                Commencer gratuitement
              </Link>
              <Link 
                to="/login"
                className="bg-transparent border-2 border-white text-white px-8 py-4 rounded-lg font-bold text-lg hover:bg-white hover:text-indigo-600 transition"
              >
                Déjà client ? Se connecter
              </Link>
            </div>
            <p className="text-indigo-200 mt-4 text-sm">
              ✓ Essai gratuit • ✓ Sans engagement • ✓ Résiliation à tout moment
            </p>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-8">
            <div className="col-span-2 md:col-span-1">
              <div className="flex items-center space-x-2 mb-4">
                <Plane className="h-6 w-6" />
                <span className="text-xl font-bold">GlobeGenius</span>
              </div>
              <p className="text-gray-400">
                L'IA qui révolutionne la façon de voyager moins cher.
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold mb-4">Produit</h4>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#features" className="hover:text-white">Fonctionnalités</a></li>
                <li><a href="#pricing" className="hover:text-white">Tarifs</a></li>
                <li><Link to="/api" className="hover:text-white">API</Link></li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-4">Entreprise</h4>
              <ul className="space-y-2 text-gray-400">
                <li><Link to="/about" className="hover:text-white">À propos</Link></li>
                <li><Link to="/blog" className="hover:text-white">Blog</Link></li>
                <li><Link to="/careers" className="hover:text-white">Carrières</Link></li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-4">Support</h4>
              <ul className="space-y-2 text-gray-400">
                <li><Link to="/help" className="hover:text-white">Centre d'aide</Link></li>
                <li><Link to="/contact" className="hover:text-white">Contact</Link></li>
                <li><Link to="/privacy" className="hover:text-white">Confidentialité</Link></li>
                <li><Link to="/terms" className="hover:text-white">CGU</Link></li>
              </ul>
            </div>
          </div>
          
          <div className="border-t border-gray-800 pt-8 text-center text-gray-400">
            <p>&copy; {new Date().getFullYear()} GlobeGenius. Tous droits réservés.</p>
            {apiStatus === 'healthy' && (
              <span className="inline-block w-2 h-2 bg-green-500 rounded-full ml-2" title="API connectée"></span>
            )}
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;