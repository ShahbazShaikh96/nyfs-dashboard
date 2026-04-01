type Props = {
  photoUrl: string | null | undefined;
  restaurantName: string;
  cuisineType: string;
};

export function RestaurantPhoto({ photoUrl, restaurantName, cuisineType }: Props) {
  const fallback = `https://placehold.co/420x220/e2e8f0/334155?text=${encodeURIComponent(
    cuisineType || "Restaurant"
  )}`;

  return (
    <img
      src={photoUrl || fallback}
      alt={`Photo for ${restaurantName}`}
      className="restaurant-photo"
      loading="lazy"
      onError={(event) => {
        if (event.currentTarget.src !== fallback) {
          event.currentTarget.src = fallback;
        }
      }}
    />
  );
}
