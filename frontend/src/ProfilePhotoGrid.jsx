import './Profile.css';

// Grid of photo tiles used on both the own profile and public profiles.
// When `onSelect` is passed, each tile is a button that opens the photo page.
function ProfilePhotoGrid({ photos, onSelect }) {
    return (
        <div className="pr-grid">
            {photos.map((photo) => {
                const rating = Number(photo.average_rating || 0);
                const tile = (
                    <>
                        <img className="pr-tile__img" src={photo.url} alt="" loading="lazy" />
                        <span className="pr-tile__body">
                            <span className={photo.description ? 'pr-tile__text' : 'pr-tile__text is-empty'}>{photo.description || 'No description'}</span>
                            <span className={rating ? 'pr-tile__rating' : 'pr-tile__rating is-empty'}>{rating ? `★ ${rating.toFixed(1)}` : 'Not rated'}</span>
                        </span>
                    </>
                );

                return onSelect ? (
                    <button className="pr-tile" type="button" key={photo.id} onClick={() => onSelect(photo.id)}>{tile}</button>
                ) : (
                    <div className="pr-tile" key={photo.id}>{tile}</div>
                );
            })}
        </div>
    );
}

export default ProfilePhotoGrid;