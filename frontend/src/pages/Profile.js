
import React, { useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

const Profile = () => {
  const { user } = useAuth();
  
  useEffect(() => {
    console.log("Profile component mounted");
    console.log("Current user:", user);
  }, [user]);

  return (
    <div className="p-8 bg-white">
      <h1 className="text-2xl font-bold text-blue-600">Profil</h1>
      <p className="mt-4">Page en construction...</p>
      {user ? (
        <div className="mt-4 p-4 border rounded shadow-sm">
          <p><strong>Email:</strong> {user.email}</p>
          <p><strong>Nom:</strong> {user.name || 'Non défini'}</p>
        </div>
      ) : (
        <p className="mt-4 text-red-500">Utilisateur non connecté</p>
      )}
    </div>
  );
};

export default Profile;