import { Link } from 'react-router-dom';
import './Home.css';

function Home() {
  return (
    <section className="home">
      <div className="home-overlay">
        <div className="home-content">
          <h1>Descubre tu próxima aventura</h1>

          <p>
            Encuentra destinos increíbles, paquetes turísticos y experiencias
            inolvidables con Travelers.
          </p>

          <Link to="/packages" className="home-button">
            Descubre paquetes turísticos
          </Link>
        </div>
      </div>
    </section>
  );
}

export default Home;